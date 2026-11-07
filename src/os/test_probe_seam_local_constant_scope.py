"""AC-PLC1..AC-PLC6 suite for the seam local-constant scope face (R2523).

Criteria were pinned in state/queue/tech.md:559 at R2521 BEFORE this code
existed.

What this proves: MEASURED at R2521 in the constant-binding face legs, a probe
that declares its module name inside a function body reads OUT-OF-SCOPE,
because that face reads its constant table off module-level assignments only,
and a container reached through an attribute was not resolved either. This
face resolves a dynamic module name through string constants declared in the
enclosing FUNCTION body and through a constant-key lookup into a module-level
container reached by a plain attribute on a module bound in the same root, on
the same cycle-guarded same-root walk, so such a probe is answered on its own
row instead of being skipped. A name built by a real call or a comprehension is
never guessed at and never evaluated.

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

import probe_seam_dynamic_import_scope as PDI  # noqa: E402
import probe_seam_local_constant_scope as PLC  # noqa: E402
import probe_seam_registry as PSR  # noqa: E402
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "probe_seam_local_constant_scope.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
RENDER_MODULE = os.path.join(SANDBOX, "suite_matrix.py")
WIRED_LABEL = '"os-probe-seam-local-constant-scope",'
WIRED_SUITE = '"test_probe_seam_local_constant_scope.py"), 6),'

HELPER = "plc_helper"
PARTIAL = "plc_partial"
CFG = "plc_cfg"
MARKER = "plc_import_marker.txt"

LOCAL_FIXTURE = ('import importlib\n'
                 '\n'
                 'def run():\n'
                 '    name = "%s"\n'
                 '    return importlib.import_module(name).QUIETED\n')

CONTAINER_FIXTURE = ('import importlib\n'
                     'import %s\n'
                     '\n'
                     'def run():\n'
                     '    return importlib.import_module(%s.NAMES[1]).QUIETED\n'
                     % (CFG, CFG))

LOCAL_COMPUTED_FIXTURE = ('import importlib\n'
                          '\n'
                          'def run():\n'
                          '    name = "plc_" + "helper"\n'
                          '    return importlib.import_module(name).QUIETED\n')

CALLED_CONTAINER_FIXTURE = ('import importlib\n'
                            'import %s\n'
                            '\n'
                            'def run():\n'
                            '    return importlib.import_module('
                            '%s.names()[0]).QUIETED\n' % (CFG, CFG))


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
        code = PLC.main(["module.py"] + argv)
    return code, buffer.getvalue()


class World(object):
    """A private root with the helpers and one config module every leg needs."""

    def __init__(self, with_partial=True):
        self.path = tempfile.mkdtemp(prefix="plc-suite-")
        self.seams = PLC.seam_names(SM)
        write_ascii(os.path.join(self.path, HELPER + ".py"),
                    helper_text(self.seams) + marker_line())
        if with_partial:
            write_ascii(os.path.join(self.path, PARTIAL + ".py"),
                        helper_text(self.seams, omit=self.seams[:1])
                        + marker_line())
        write_ascii(os.path.join(self.path, CFG + ".py"),
                    'NAMES = ("plc_unused", "%s")\n'
                    '\n'
                    'def names():\n'
                    '    return ("plc_unused", "%s")\n' % (HELPER, HELPER))

    def write(self, name, text):
        write_ascii(os.path.join(self.path, name), text)
        return name

    def close(self):
        shutil.rmtree(self.path, ignore_errors=True)


def ac_plc1():
    """The local table is read off the probe tree; nothing is evaluated."""
    seams = PLC.seam_names(SM)
    source_text = read_text(MODULE)
    ok = check(not [name for name in seams if name in source_text],
               "AC-PLC1 no seam name is spelled in the module source")
    ok = check(not [name for name in (HELPER, PARTIAL, CFG)
                    if name in source_text],
               "AC-PLC1 no fixture helper or config name is written into the "
               "module") and ok
    local = PLC.local_bindings(LOCAL_FIXTURE % HELPER)
    ok = check(local == {"name": (PLC.SHAPE_STR, HELPER)},
               "AC-PLC1 a function-body str literal is read off the tree "
               "(%r)" % (local,)) and ok
    local = PLC.local_bindings(LOCAL_COMPUTED_FIXTURE)
    ok = check(local == {},
               "AC-PLC1 a function-body computation is NOT a local constant "
               "(%r)" % (local,)) and ok
    local = PLC.local_bindings('def a():\n'
                               '    name = "plc_helper"\n'
                               'def b():\n'
                               '    name = "plc_other"\n')
    ok = check(local == {},
               "AC-PLC1 an ambiguous local name is NOT resolved (%r)"
               % (local,)) and ok
    module_table = PLC.module_bindings('def run():\n'
                                       '    name = "plc_helper"\n')
    ok = check(module_table == {},
               "AC-PLC1 a function-body assignment is not a module binding "
               "(%r)" % (module_table,)) and ok
    world = World(with_partial=False)
    try:
        probe = CONTAINER_FIXTURE
        got = PLC.resolve_expression("%s.NAMES[1]" % CFG, probe, world.path)
        ok = check(got == (HELPER, "%s.NAMES" % CFG),
                   "AC-PLC1 a constant-key container reached by a plain "
                   "attribute resolves (%r)" % (got,)) and ok
        got = PLC.resolve_expression("%s.names()[0]" % CFG, probe,
                                     world.path)
        ok = check(got is None,
                   "AC-PLC1 a container reached through a call is NOT "
                   "resolved (%r)" % (got,)) and ok
    finally:
        world.close()
    got = PLC.resolve_expression('"%s"' % HELPER, LOCAL_FIXTURE % HELPER)
    ok = check(got == (HELPER, ""),
               "AC-PLC1 a str literal argument resolves with no binding "
               "(%r)" % (got,)) and ok
    return ok


def ac_plc2():
    """A function-body constant reads COVERED with helper, binding and shape."""
    world = World(with_partial=False)
    try:
        world.write("plc_local.py", LOCAL_FIXTURE % HELPER)
        world.write("plc_container.py", CONTAINER_FIXTURE)
        report = PLC.audit(world.path, SM)
        ok = True
        for name, binding in (("plc_local.py", "name"),
                              ("plc_container.py", "%s.NAMES" % CFG)):
            row = row_of(report, name)
            expected = "%s:%s@%s" % (PDI.SHAPE_IMPORTLIB, HELPER, binding)
            ok = check(row.get("verdict") == PLC.COVERED
                       and HELPER in row.get("helpers", [])
                       and expected in row.get("dynamic", []),
                       "AC-PLC2 %s reads COVERED with helper=%s binding=%s "
                       "(%r)" % (name, HELPER, binding,
                                 (row.get("verdict"), row.get("helpers"),
                                  row.get("dynamic")))) and ok
        local_row = row_of(report, "plc_local.py")
        ok = check(local_row.get("local_bindings") == ["name"],
                   "AC-PLC2 the row names the local binding it read (%r)"
                   % (local_row.get("local_bindings"),)) and ok
        ok = check(len(row_of(report, "plc_local.py").get("quieted", []))
                   == len(world.seams),
                   "AC-PLC2 the local probe really quiets every seam (%r)"
                   % (len(row_of(report, "plc_local.py").get("quieted", [])),)) \
            and ok
        ok = check(report["verdict"] == PLC.SEAMS_COVERED,
                   "AC-PLC2 the whole world reads %s (%s)"
                   % (PLC.SEAMS_COVERED, report["verdict"])) and ok
        return ok
    finally:
        world.close()


def ac_plc3():
    """Such a binding reaching a partial helper reads MISSING-SEAM, never run."""
    world = World()
    try:
        world.write("plc_partial_probe.py",
                    LOCAL_FIXTURE % PARTIAL)
        report = PLC.audit(world.path, SM)
        row = row_of(report, "plc_partial_probe.py")
        ok = check(row.get("verdict") == PLC.MISSING_SEAM
                   and row.get("missing") == world.seams[:1],
                   "AC-PLC3 a local constant reaching a partial helper reads "
                   "MISSING-SEAM naming seam and probe (%r)"
                   % ((row.get("verdict"), row.get("missing")),))
        ok = check(report["verdict"] == PLC.SEAMS_STALE,
                   "AC-PLC3 the world verdict is %s (%s)"
                   % (PLC.SEAMS_STALE, report["verdict"])) and ok
        ok = check(not os.path.isfile(os.path.join(world.path, MARKER)),
                   "AC-PLC3 neither probe nor helper was imported or run") \
            and ok
        code, out = call_main(["--root", world.path])
        ok = check(code == 2 and "MISSING-SEAM" in out,
                   "AC-PLC3 the CLI refuses with exit 2 (%d)" % code) and ok
        return ok
    finally:
        world.close()


def ac_plc4():
    """A name built by a call or a comprehension is named, never resolved."""
    world = World()
    try:
        world.write("plc_local_computed.py", LOCAL_COMPUTED_FIXTURE)
        world.write("plc_called_container.py", CALLED_CONTAINER_FIXTURE)
        world.write("plc_comprehension.py",
                    'import importlib\n'
                    '\n'
                    'def run():\n'
                    '    names = [x for x in ("plc_unused", "%s")]\n'
                    '    return importlib.import_module(names[1]).QUIETED\n'
                    % HELPER)
        report = PLC.audit(world.path, SM)
        ok = True
        for name in ("plc_local_computed.py", "plc_called_container.py",
                     "plc_comprehension.py"):
            row = row_of(report, name)
            ok = check(row.get("verdict") == PLC.OUT_OF_SCOPE
                       and row.get("unresolved")
                       and not row.get("quieted"),
                       "AC-PLC4 %s reads OUT-OF-SCOPE with the call named "
                       "(%r)" % (name, (row.get("verdict"),
                                        row.get("unresolved")))) and ok
            ok = check(not [item for item in row.get("dynamic", [])
                            if item.endswith("@" + HELPER)],
                       "AC-PLC4 %s is not resolved to %s (%r)"
                       % (name, HELPER, row.get("dynamic"))) and ok
        got = PLC.dynamic_imports(LOCAL_COMPUTED_FIXTURE, world.path)
        ok = check(got is not None and got["unresolved"] == [
            "importlib.import_module:name"],
            "AC-PLC4 the computed call is reported verbatim (%r)"
            % (got,)) and ok
        got = PLC.resolve_expression("%s.names()[0]" % CFG,
                                     CALLED_CONTAINER_FIXTURE, world.path)
        ok = check(got is None,
                   "AC-PLC4 a module-level container reached through a call "
                   "is not resolved (%r)" % (got,)) and ok
        got = PLC.resolve_expression('"plc_" + "helper"',
                                     LOCAL_COMPUTED_FIXTURE, world.path)
        ok = check(got is None,
                   "AC-PLC4 a concatenation is not resolved (%r)"
                   % (got,)) and ok
        return ok
    finally:
        world.close()


def ac_plc5():
    """The reading is read-only: no digest moves, no marker lands."""
    world = World()
    try:
        world.write("plc_local.py", LOCAL_FIXTURE % HELPER)
        world.write("plc_local_computed.py", LOCAL_COMPUTED_FIXTURE)
        before = dict((name, digest(os.path.join(world.path, name)))
                      for name in sorted(os.listdir(world.path)))
        module_before = digest(MODULE)
        render_before = digest(RENDER_MODULE)
        PLC.audit(world.path, SM)
        PLC.reading(world.path, SM)
        after = dict((name, digest(os.path.join(world.path, name)))
                     for name in sorted(os.listdir(world.path)))
        ok = check(before == after and not os.path.isfile(
            os.path.join(world.path, MARKER)),
            "AC-PLC5 every fixture digest is unchanged and nothing landed")
        ok = check(digest(MODULE) == module_before
                   and digest(RENDER_MODULE) == render_before,
                   "AC-PLC5 the shipped module and render are unchanged") \
            and ok
        refused = PLC.reading(os.path.join(world.path, "no-such-root"), SM)
        ok = check(refused.get("refusal") == PLC.E_NO_ROOT
                   and refused["verdict"] == PLC.SEAMS_STALE,
                   "AC-PLC5 a missing root is refused, not silently clean") \
            and ok
        return ok
    finally:
        world.close()


def ac_plc6():
    """Pure ASCII, stdlib only, no clock, no network, wired once."""
    text = read_text(MODULE)
    suite = read_text(os.path.abspath(__file__))
    ok = check(all(ord(char) < 128 for char in text),
               "AC-PLC6 the module source is pure ASCII")
    ok = check(all(ord(char) < 128 for char in suite),
               "AC-PLC6 this suite source is pure ASCII") and ok
    imports = sorted(set(re.findall(r"(?m)^import ([A-Za-z_][A-Za-z0-9_]*)",
                                   text)))
    allowed = ("argparse", "ast", "hashlib", "json", "os", "re", "sys",
               "warnings")
    ok = check(not [name for name in imports if name not in allowed],
               "AC-PLC6 only the allowed stdlib modules are imported (%s)"
               % (",".join(imports),)) and ok
    forbidden = ("time.time", "datetime", "socket", "urllib", "requests",
                 "http.client", "subprocess")
    ok = check(not [token for token in forbidden if token in text],
               "AC-PLC6 no clock and no network token in the module") and ok
    registry = read_text(REGISTRY)
    ok = check(WIRED_LABEL in registry and WIRED_SUITE in registry,
               "AC-PLC6 the face and its suite are wired into the registry "
               "exactly once") and ok
    ok = check(registry.count(WIRED_LABEL) == 1
               and registry.count(WIRED_SUITE) == 1,
               "AC-PLC6 no duplicate registry row") and ok
    ok = check(PLC.LABEL == "os-probe-seam-local-constant-scope",
               "AC-PLC6 the reconcile label is the face own (%s)"
               % PLC.LABEL) and ok
    return ok


def main():
    print("PROBE SEAM LOCAL CONSTANT SCOPE SUITE (AC-PLC1..AC-PLC6)")
    results = [ac_plc1(), ac_plc2(), ac_plc3(), ac_plc4(), ac_plc5(), ac_plc6()]
    passed = len([item for item in results if item])
    print("SUITE %s %d/%d criteria green"
          % ("PASS" if passed == EXPECTED_CRITERIA else "FAIL",
             passed, EXPECTED_CRITERIA))
    return 0 if passed == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())