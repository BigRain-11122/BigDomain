"""AC-PLAC1..AC-PLAC6 suite for the seam annotated-constant scope face (R2525).

Criteria were pinned in state/queue/tech.md:561 at R2523 BEFORE this code
existed.

What this proves: MEASURED at R2523 on the shipped local-constant face own
readers, an annotated assignment (`NAME: str = "x"`), a walrus binding and a
for-loop target of a str literal all read {} from the constant tables, and a
container reached through a nested attribute (`pkg.CFG.NAMES[0]`) resolved to
None - so a probe written in any of those shapes read OUT-OF-SCOPE. This face
reads those shapes on the same cycle-guarded same-root walk, so such a probe is
answered on its own row with the binding label it was followed through. A
value built by a call, a comprehension or a run-time expression is never
evaluated and never resolved, and an annotated assignment whose annotation is
not a plain name is refused rather than guessed.

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

import probe_seam_annotated_constant_scope as PLAC  # noqa: E402
import probe_seam_dynamic_import_scope as PDI  # noqa: E402
import probe_seam_local_constant_scope as PLC  # noqa: E402
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "probe_seam_annotated_constant_scope.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
RENDER_MODULE = os.path.join(SANDBOX, "suite_matrix.py")
WIRED_LABEL = '"os-probe-seam-annotated-constant-scope",'
WIRED_SUITE = '"test_probe_seam_annotated_constant_scope.py"), 6),'

HELPER = "plac_helper"
PARTIAL = "plac_partial"
PKG = "plac_pkg"
MARKER = "plac_import_marker.txt"

ANNOTATED_MODULE_FIXTURE = ('import importlib\n'
                            '\n'
                            'NAME: str = "%s"\n'
                            '\n'
                            'def run():\n'
                            '    return importlib.import_module(NAME).QUIETED\n'
                            % HELPER)

ANNOTATED_LOCAL_FIXTURE = ('import importlib\n'
                           '\n'
                           'def run():\n'
                           '    name: str = "%s"\n'
                           '    return importlib.import_module(name).QUIETED\n'
                           % HELPER)

WALRUS_FIXTURE = ('import importlib\n'
                  '\n'
                  'def run():\n'
                  '    if (name := "%s"):\n'
                  '        return importlib.import_module(name).QUIETED\n'
                  % HELPER)

FOR_FIXTURE = ('import importlib\n'
               '\n'
               'def run():\n'
               '    for name in ("%s",):\n'
               '        return importlib.import_module(name).QUIETED\n'
               % HELPER)

NESTED_FIXTURE = ('import importlib\n'
                  'import %s\n'
                  '\n'
                  'def run():\n'
                  '    return importlib.import_module('
                  '%s.CFG.NAMES[1]).QUIETED\n' % (PKG, PKG))

COMPUTED_FIXTURE = ('import importlib\n'
                    '\n'
                    'def run():\n'
                    '    name = "plac_" + "helper"\n'
                    '    return importlib.import_module(name).QUIETED\n')

COMPREHENSION_FIXTURE = ('import importlib\n'
                         '\n'
                         'def run():\n'
                         '    name = [x for x in ("plac_unused", "%s")][1]\n'
                         '    return importlib.import_module(name).QUIETED\n'
                         % HELPER)

OPAQUE_ANNOTATION_FIXTURE = ('import importlib\n'
                             'from typing import Dict\n'
                             '\n'
                             'NAMES: Dict[str, str] = {"x": "%s"}\n'
                             '\n'
                             'def run():\n'
                             '    return importlib.import_module('
                             'NAMES["x"]).QUIETED\n' % HELPER)


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


def call_main(argv):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = PLAC.main(["module.py"] + argv)
    return code, buffer.getvalue()


class World(object):
    """A private root with the helpers and one package module."""

    def __init__(self, with_partial=True):
        self.path = tempfile.mkdtemp(prefix="plac-suite-")
        self.seams = PLAC.seam_names(SM)
        write_ascii(os.path.join(self.path, HELPER + ".py"),
                    helper_text(self.seams) + marker_line())
        if with_partial:
            write_ascii(os.path.join(self.path, PARTIAL + ".py"),
                        helper_text(self.seams, omit=self.seams[:1])
                        + marker_line())
        write_ascii(os.path.join(self.path, PKG + ".py"),
                    'NAMES = ("plac_unused", "%s")\n'
                    'CFG = {"NAMES": ("plac_unused", "%s")}\n'
                    % (HELPER, HELPER))

    def write(self, name, text):
        write_ascii(os.path.join(self.path, name), text)
        return name

    def close(self):
        shutil.rmtree(self.path, ignore_errors=True)


def ac_plac1():
    """The extended table is read off the tree; only constants enter it."""
    seams = PLAC.seam_names(SM)
    source_text = read_text(MODULE)
    ok = check(not [name for name in seams if name in source_text],
               "AC-PLAC1 no seam name is spelled in the module source")
    ok = check(not [name for name in (HELPER, PARTIAL, PKG)
                    if name in source_text],
               "AC-PLAC1 no fixture module name is written into the module") \
        and ok
    table = PLAC.module_bindings(ANNOTATED_MODULE_FIXTURE)
    ok = check(table.get("NAME") == (PLAC.TREE_STR, HELPER),
               "AC-PLAC1 a module-level annotated str literal is read "
               "(%r)" % (table,)) and ok
    table = PLAC.module_bindings('NAME: str = "plac_" + "helper"\n')
    ok = check("NAME" not in table,
               "AC-PLAC1 an annotated computation is NOT a constant (%r)"
               % (table,)) and ok
    table = PLAC.module_bindings('NAMES: Dict[str, str] = {"x": "%s"}\n'
                                 % HELPER)
    ok = check("NAMES" not in table,
               "AC-PLAC1 an annotation that is not a plain name is refused "
               "(%r)" % (table,)) and ok
    local = PLAC.local_bindings(WALRUS_FIXTURE)
    ok = check(local.get("name") == (PLAC.TREE_STR, HELPER),
               "AC-PLAC1 a function-body walrus binding is read (%r)"
               % (local,)) and ok
    local = PLAC.local_bindings(FOR_FIXTURE)
    ok = check(local.get("name") == (PLAC.TREE_STR, HELPER),
               "AC-PLAC1 a for-loop target of one str literal is read (%r)"
               % (local,)) and ok
    local = PLAC.local_bindings('def a():\n'
                                '    name: str = "plac_helper"\n'
                                'def b():\n'
                                '    name: str = "plac_other"\n')
    ok = check(local == {},
               "AC-PLAC1 an ambiguous annotated name is NOT resolved (%r)"
               % (local,)) and ok
    world = World(with_partial=False)
    try:
        got = PLAC.resolve_expression("%s.CFG.NAMES[1]" % PKG, NESTED_FIXTURE,
                                      world.path)
        ok = check(got == (HELPER, "%s.CFG.NAMES" % PKG),
                   "AC-PLAC1 a nested attribute chain resolves with its "
                   "binding label (%r)" % (got,)) and ok
        got = PLAC.resolve_expression("%s.CFG.names()[0]" % PKG,
                                      NESTED_FIXTURE, world.path)
        ok = check(got is None,
                   "AC-PLAC1 a chain through a call is NOT resolved (%r)"
                   % (got,)) and ok
    finally:
        world.close()
    return ok


def ac_plac2():
    """Each extended shape reads COVERED with helper, binding and shape."""
    world = World(with_partial=False)
    try:
        legs = (("plac_annotated_module.py", ANNOTATED_MODULE_FIXTURE, "NAME"),
                ("plac_annotated_local.py", ANNOTATED_LOCAL_FIXTURE, "name"),
                ("plac_walrus.py", WALRUS_FIXTURE, "name"),
                ("plac_for.py", FOR_FIXTURE, "name"),
                ("plac_nested.py", NESTED_FIXTURE,
                 "%s.CFG.NAMES" % PKG))
        for name, text, binding in legs:
            world.write(name, text)
        report = PLAC.audit(world.path, SM)
        ok = True
        for name, _text, binding in legs:
            row = row_of(report, name)
            expected = "%s:%s@%s" % (PDI.SHAPE_IMPORTLIB, HELPER, binding)
            ok = check(row.get("verdict") == PLAC.COVERED
                       and HELPER in row.get("helpers", [])
                       and expected in row.get("dynamic", []),
                       "AC-PLAC2 %s reads COVERED with helper=%s binding=%s "
                       "(%r)" % (name, HELPER, binding,
                                 (row.get("verdict"), row.get("helpers"),
                                  row.get("dynamic")))) and ok
        ok = check(row_of(report, "plac_annotated_module.py").get(
            "module_bindings") == ["NAME"],
                   "AC-PLAC2 the row names the module binding it read (%r)"
                   % (row_of(report, "plac_annotated_module.py").get(
                       "module_bindings"),)) and ok
        ok = check(row_of(report, "plac_annotated_local.py").get(
            "local_bindings") == ["name"],
                   "AC-PLAC2 the row names the local binding it read (%r)"
                   % (row_of(report, "plac_annotated_local.py").get(
                       "local_bindings"),)) and ok
        ok = check(len(row_of(report, "plac_walrus.py").get("quieted", []))
                   == len(world.seams),
                   "AC-PLAC2 a walrus probe really quiets every seam (%r)"
                   % (len(row_of(report, "plac_walrus.py").get(
                       "quieted", [])),)) and ok
        ok = check(report["verdict"] == PLAC.SEAMS_COVERED,
                   "AC-PLAC2 the whole world reads %s (%s)"
                   % (PLAC.SEAMS_COVERED, report["verdict"])) and ok
        return ok
    finally:
        world.close()


def ac_plac3():
    """Such a binding reaching a partial helper reads MISSING-SEAM, never run."""
    world = World()
    try:
        world.write("plac_partial_probe.py",
                    'import importlib\n'
                    '\n'
                    'NAME: str = "%s"\n'
                    '\n'
                    'def run():\n'
                    '    return importlib.import_module(NAME).QUIETED\n'
                    % PARTIAL)
        report = PLAC.audit(world.path, SM)
        row = row_of(report, "plac_partial_probe.py")
        ok = check(row.get("verdict") == PLAC.MISSING_SEAM
                   and row.get("missing") == world.seams[:1],
                   "AC-PLAC3 an annotated binding reaching a partial helper "
                   "reads MISSING-SEAM naming seam and probe (%r)"
                   % ((row.get("verdict"), row.get("missing")),))
        ok = check(report["verdict"] == PLAC.SEAMS_STALE,
                   "AC-PLAC3 the world verdict is %s (%s)"
                   % (PLAC.SEAMS_STALE, report["verdict"])) and ok
        ok = check(not os.path.isfile(os.path.join(world.path, MARKER)),
                   "AC-PLAC3 neither probe nor helper was imported or run") \
            and ok
        code, out = call_main(["--root", world.path])
        ok = check(code == 2 and "MISSING-SEAM" in out,
                   "AC-PLAC3 the CLI refuses with exit 2 (%d)" % code) and ok
        return ok
    finally:
        world.close()


def ac_plac4():
    """Computed values and opaque annotations are named, never resolved."""
    world = World()
    try:
        world.write("plac_computed.py", COMPUTED_FIXTURE)
        world.write("plac_comprehension.py", COMPREHENSION_FIXTURE)
        world.write("plac_opaque.py", OPAQUE_ANNOTATION_FIXTURE)
        report = PLAC.audit(world.path, SM)
        ok = True
        for name in ("plac_computed.py", "plac_comprehension.py",
                     "plac_opaque.py"):
            row = row_of(report, name)
            ok = check(row.get("verdict") == PLAC.OUT_OF_SCOPE
                       and row.get("unresolved")
                       and not row.get("quieted"),
                       "AC-PLAC4 %s reads OUT-OF-SCOPE with the name "
                       "reported (%r)" % (name, (row.get("verdict"),
                                                 row.get("unresolved")))) \
                and ok
            ok = check(not [item for item in row.get("dynamic", [])
                            if item.endswith("@" + HELPER)],
                       "AC-PLAC4 %s is not resolved to %s (%r)"
                       % (name, HELPER, row.get("dynamic"))) and ok
        got = PLAC.dynamic_imports(COMPUTED_FIXTURE, world.path)
        ok = check(got is not None and got["unresolved"] == [
            "importlib.import_module:name"],
            "AC-PLAC4 the computed call is reported verbatim (%r)"
            % (got,)) and ok
        ok = check(PLAC.resolve_expression('"plac_" + "helper"',
                                           COMPUTED_FIXTURE,
                                           world.path) is None,
                   "AC-PLAC4 a concatenation is not resolved") and ok
        ok = check(PLAC.resolve_expression(
            '%s.CFG.NAMES[0] + "_helper"' % PKG, NESTED_FIXTURE,
            world.path) is None,
                   "AC-PLAC4 an arithmetic expression is not resolved") and ok
        return ok
    finally:
        world.close()


def ac_plac5():
    """The reading is read-only: no digest moves, no marker lands."""
    world = World()
    try:
        world.write("plac_annotated_module.py", ANNOTATED_MODULE_FIXTURE)
        world.write("plac_nested.py", NESTED_FIXTURE)
        world.write("plac_computed.py", COMPUTED_FIXTURE)
        before = dict((name, digest(os.path.join(world.path, name)))
                      for name in sorted(os.listdir(world.path)))
        module_before = digest(MODULE)
        render_before = digest(RENDER_MODULE)
        PLAC.audit(world.path, SM)
        PLAC.reading(world.path, SM)
        after = dict((name, digest(os.path.join(world.path, name)))
                     for name in sorted(os.listdir(world.path)))
        ok = check(before == after and not os.path.isfile(
            os.path.join(world.path, MARKER)),
            "AC-PLAC5 every fixture digest is unchanged and nothing landed")
        ok = check(digest(MODULE) == module_before
                   and digest(RENDER_MODULE) == render_before,
                   "AC-PLAC5 the shipped module and render are unchanged") \
            and ok
        refused = PLAC.reading(os.path.join(world.path, "no-such-root"), SM)
        ok = check(refused.get("refusal") == PLAC.E_NO_ROOT
                   and refused["verdict"] == PLAC.SEAMS_STALE,
                   "AC-PLAC5 a missing root is refused, not silently clean") \
            and ok
        return ok
    finally:
        world.close()


def ac_plac6():
    """Pure ASCII, stdlib only, no clock, no network, wired once."""
    text = read_text(MODULE)
    suite = read_text(os.path.abspath(__file__))
    ok = check(all(ord(char) < 128 for char in text),
               "AC-PLAC6 the module source is pure ASCII")
    ok = check(all(ord(char) < 128 for char in suite),
               "AC-PLAC6 this suite source is pure ASCII") and ok
    imports = sorted(set(re.findall(r"(?m)^import ([A-Za-z_][A-Za-z0-9_]*)",
                                   text)))
    allowed = ("argparse", "ast", "hashlib", "json", "os", "re", "sys",
               "warnings")
    ok = check(not [name for name in imports if name not in allowed],
               "AC-PLAC6 only the allowed stdlib modules are imported (%s)"
               % (",".join(imports),)) and ok
    forbidden = ("time.time", "datetime", "socket", "urllib", "requests",
                 "http.client", "subprocess")
    ok = check(not [token for token in forbidden if token in text],
               "AC-PLAC6 no clock and no network token in the module") and ok
    registry = read_text(REGISTRY)
    ok = check(WIRED_LABEL in registry and WIRED_SUITE in registry,
               "AC-PLAC6 the face and its suite are wired into the registry "
               "exactly once") and ok
    ok = check(registry.count(WIRED_LABEL) == 1
               and registry.count(WIRED_SUITE) == 1,
               "AC-PLAC6 no duplicate registry row") and ok
    ok = check(PLAC.LABEL == "os-probe-seam-annotated-constant-scope",
               "AC-PLAC6 the reconcile label is the face own (%s)"
               % PLAC.LABEL) and ok
    ok = check(PLAC.SEAMS_COVERED == "SEAMS-ANNOTATED-COVERED",
               "AC-PLAC6 the reading has its own verdict word (%s)"
               % PLAC.SEAMS_COVERED) and ok
    return ok


def main():
    print("PROBE SEAM ANNOTATED CONSTANT SCOPE SUITE (AC-PLAC1..AC-PLAC6)")
    results = [ac_plac1(), ac_plac2(), ac_plac3(), ac_plac4(), ac_plac5(),
               ac_plac6()]
    passed = len([item for item in results if item])
    print("SUITE %s %d/%d criteria green"
          % ("PASS" if passed == EXPECTED_CRITERIA else "FAIL",
             passed, EXPECTED_CRITERIA))
    return 0 if passed == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())