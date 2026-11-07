"""AC-PCAS1..AC-PCAS6 suite for the seam constant-alias scope face (R2527).

Criteria were pinned in state/queue/tech.md:563 at R2525 BEFORE this code
existed.

What this proves: MEASURED at R2525 on the annotated face own readers, an
annotated alias of an existing constant (`ALIAS: str = BASE_NAME`) read the
table with ALIAS ABSENT, a with-as binding and a for-loop target over two or
more literals read empty, and a deep dict chain was not followed - so those
shapes were indistinguishable from a name never declared. This face follows an
alias of an alias to a fixpoint, NAMES the shapes that are genuinely not
constants, and either resolves a deep chain with its full label or names the
hop that broke.

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

import probe_seam_constant_alias_scope as PCAS  # noqa: E402
import probe_seam_annotated_constant_scope as PLAC  # noqa: E402
import probe_seam_dynamic_import_scope as PDI  # noqa: E402
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "probe_seam_constant_alias_scope.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
RENDER_MODULE = os.path.join(SANDBOX, "suite_matrix.py")
WIRED_LABEL = '"os-probe-seam-constant-alias-scope",'
WIRED_SUITE = '"test_probe_seam_constant_alias_scope.py"), 6),'

HELPER = "pcas_helper"
PARTIAL = "pcas_partial"
PKG = "pcas_pkg"
MARKER = "pcas_import_marker.txt"

ALIAS_MODULE_FIXTURE = ('import importlib\n'
                        '\n'
                        'BASE_NAME = "%s"\n'
                        'ALIAS: str = BASE_NAME\n'
                        '\n'
                        'def run():\n'
                        '    return importlib.import_module(ALIAS).QUIETED\n'
                        % HELPER)

ALIAS_LOCAL_FIXTURE = ('import importlib\n'
                       '\n'
                       'BASE_NAME = "%s"\n'
                       '\n'
                       'def run():\n'
                       '    if (alias := BASE_NAME):\n'
                       '        return importlib.import_module(alias).QUIETED\n'
                       % HELPER)

CHAIN_FIXTURE = ('import importlib\n'
                 '\n'
                 'BASE_NAME = "%s"\n'
                 'ALIAS: str = BASE_NAME\n'
                 'SECOND: str = ALIAS\n'
                 '\n'
                 'def run():\n'
                 '    return importlib.import_module(SECOND).QUIETED\n'
                 % HELPER)

WITH_FIXTURE = ('import importlib\n'
                '\n'
                'def run():\n'
                '    with open("pcas_marker.txt") as handle:\n'
                '        return importlib.import_module(handle).QUIETED\n')

FOR_MULTI_FIXTURE = ('import importlib\n'
                     '\n'
                     'def run():\n'
                     '    for name in ("%s", "pcas_other"):\n'
                     '        return importlib.import_module(name).QUIETED\n'
                     % HELPER)

CALL_FIXTURE = ('import importlib\n'
                '\n'
                'def run():\n'
                '    name = "".join(("pcas_", "helper"))\n'
                '    return importlib.import_module(name).QUIETED\n')

FORMAT_FIXTURE = ('import importlib\n'
                  '\n'
                  'def run():\n'
                  '    name = "pcas_%s" % "helper"\n'
                  '    return importlib.import_module(name).QUIETED\n')


def check(ok, label):
    if ok:
        print("PASS %s" % label)
    else:
        print("FAIL %s" % label)
    return ok


def read_text(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


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
        code = PCAS.main(["module.py"] + argv)
    return code, buffer.getvalue()


class World(object):
    """A private root with the helpers and one package module."""

    def __init__(self, with_partial=False):
        self.path = tempfile.mkdtemp(prefix="pcas-suite-")
        self.seams = PCAS.seam_names(SM)
        write_ascii(os.path.join(self.path, HELPER + ".py"),
                    helper_text(self.seams) + marker_line())
        if with_partial:
            write_ascii(os.path.join(self.path, PARTIAL + ".py"),
                        helper_text(self.seams, omit=self.seams[:1])
                        + marker_line())
        write_ascii(os.path.join(self.path, PKG + ".py"),
                    'NAMES = ("pcas_unused", "%s")\n'
                    'CFG = {"NAMES": ("pcas_unused", "%s")}\n'
                    'DEEP = {"A": {"B": {"NAMES": ("pcas_unused", "%s")}}}\n'
                    'FLAT = {"A": "pcas_unused"}\n'
                    % (HELPER, HELPER, HELPER))

    def write(self, name, text):
        write_ascii(os.path.join(self.path, name), text)
        return name

    def close(self):
        shutil.rmtree(self.path, ignore_errors=True)


def ac_pcas1():
    """An aliased constant resolves to the SAME value and the row names it."""
    text = read_text(MODULE)
    seams = PCAS.seam_names(SM)
    ok = check(not [name for name in seams if name in text],
               "AC-PCAS1 no seam name is spelled in the module source")
    ok = check(not [name for name in (HELPER, PARTIAL, PKG)
                    if name in text],
               "AC-PCAS1 no fixture module name is written into the module") \
        and ok
    table = PCAS.module_bindings(ALIAS_MODULE_FIXTURE)
    expected = table.get("BASE_NAME")
    ok = check(expected == (PCAS.TREE_STR, HELPER)
               and table.get("ALIAS") == expected,
               "AC-PCAS1 an annotated alias reads the SAME value as its "
               "source (%r)" % (table,)) and ok
    tables = PCAS.alias_tables(ALIAS_MODULE_FIXTURE)
    ok = check("ALIAS<-BASE_NAME" in PCAS._chain_rows(tables),
               "AC-PCAS1 the alias chain it followed is published (%r)"
               % (PCAS._chain_rows(tables),)) and ok
    local = PCAS.local_bindings(ALIAS_LOCAL_FIXTURE)
    ok = check(local.get("alias") == (PCAS.TREE_STR, HELPER),
               "AC-PCAS1 a walrus alias in a function body resolves (%r)"
               % (local,)) and ok
    plain = PCAS.module_bindings('NAME: str = "%s"\n' % HELPER)
    ok = check(plain.get("NAME") == (PCAS.TREE_STR, HELPER),
               "AC-PCAS1 a plain annotated literal keeps the shipped answer "
               "(%r)" % (plain,)) and ok
    chained = PCAS.module_bindings(CHAIN_FIXTURE)
    ok = check(chained.get("SECOND") == (PCAS.TREE_STR, HELPER)
               and chained.get("ALIAS") == (PCAS.TREE_STR, HELPER),
               "AC-PCAS1 an alias of an alias resolves at the fixpoint (%r)"
               % (chained,)) and ok
    ambiguous = PCAS.module_bindings('BASE = "%s"\n'
                                     'ALIAS: str = BASE\n'
                                     'ALIAS: str = "pcas_other"\n' % HELPER)
    ok = check("ALIAS" not in ambiguous,
               "AC-PCAS1 a name bound twice is NOT resolved (%r)"
               % (ambiguous,)) and ok
    return ok


def ac_pcas2():
    """A with-as binding and a multi-value for target are NAMED, not blank."""
    world = World()
    try:
        world.write("pcas_with.py", WITH_FIXTURE)
        world.write("pcas_for_multi.py", FOR_MULTI_FIXTURE)
        report = PCAS.audit(world.path, SM)
        ok = True
        with_row = row_of(report, "pcas_with.py")
        ok = check("handle=%s" % PCAS.SHAPE_WITH in with_row.get("shapes", []),
                   "AC-PCAS2 a with-as binding is NAMED on the row (%r)"
                   % (with_row.get("shapes"),)) and ok
        for_row = row_of(report, "pcas_for_multi.py")
        ok = check("name=%s" % PCAS.SHAPE_FOR_MULTI
                   in for_row.get("shapes", []),
                   "AC-PCAS2 a multi-value for target is NAMED on the row "
                   "(%r)" % (for_row.get("shapes"),)) and ok
        ok = check(PCAS.local_bindings(WITH_FIXTURE).get("handle") is None,
                   "AC-PCAS2 a with-as binding is never resolved to a value") \
            and ok
        ok = check(PCAS.local_bindings(FOR_MULTI_FIXTURE).get("name") is None,
                   "AC-PCAS2 a multi-value for target is never resolved") \
            and ok
        ok = check(with_row.get("verdict") == PCAS.OUT_OF_SCOPE
                   and with_row.get("unresolved"),
                   "AC-PCAS2 the with-as probe reads OUT-OF-SCOPE with the "
                   "call named (%r)" % ((with_row.get("verdict"),
                                         with_row.get("unresolved")),)) and ok
        rendered = PCAS.render(report)
        ok = check(PCAS.SHAPE_WITH in rendered
                   and PCAS.SHAPE_FOR_MULTI in rendered,
                   "AC-PCAS2 both shapes are printed, not silent") and ok
        return ok
    finally:
        world.close()


def ac_pcas3():
    """A two-hop chain resolves with its full label; a broken one is named."""
    world = World()
    try:
        got, refusal = PCAS.resolve_expression("%s.CFG.NAMES[1]" % PKG,
                                               CHAIN_FIXTURE, world.path)
        ok = check(got == (HELPER, "%s.CFG.NAMES" % PKG) and refusal is None,
                   "AC-PCAS3 a one-hop dict chain resolves with its full "
                   "label (%r)" % ((got, refusal),))
        got, refusal = PCAS.resolve_expression("%s.DEEP.A.B.NAMES[1]" % PKG,
                                               CHAIN_FIXTURE, world.path)
        ok = check(got == (HELPER, "%s.DEEP.A.B.NAMES" % PKG)
                   and refusal is None,
                   "AC-PCAS3 a three-hop dict chain resolves with its full "
                   "label (%r)" % ((got, refusal),)) and ok
        got, refusal = PCAS.resolve_expression("%s.FLAT.A.NAMES[1]" % PKG,
                                               CHAIN_FIXTURE, world.path)
        ok = check(got is None and refusal is not None
                   and "not-a-dict" in refusal,
                   "AC-PCAS3 a hop that is not a dict is REFUSED by name, "
                   "not silently None (%r)" % ((got, refusal),)) and ok
        got, refusal = PCAS.resolve_expression("%s.CFG.NOSUCH[1]" % PKG,
                                               CHAIN_FIXTURE, world.path)
        ok = check(got is None and refusal is not None
                   and "no-key" in refusal,
                   "AC-PCAS3 a missing key is REFUSED by name (%r)"
                   % ((got, refusal),)) and ok
        world.write("pcas_alias_probe.py", CHAIN_FIXTURE)
        report = PCAS.audit(world.path, SM)
        row = row_of(report, "pcas_alias_probe.py")
        ok = check(row.get("verdict") == PCAS.COVERED
                   and HELPER in row.get("helpers", []),
                   "AC-PCAS3 an alias-of-alias probe reads COVERED (%r)"
                   % ((row.get("verdict"), row.get("helpers")),)) and ok
        ok = check("SECOND<-ALIAS<-BASE_NAME" in row.get("alias_chains", []),
                   "AC-PCAS3 the row carries the whole chain it followed "
                   "(%r)" % (row.get("alias_chains"),)) and ok
        return ok
    finally:
        world.close()


def ac_pcas4():
    """A call, a format and a run-time expression are named, never resolved."""
    world = World()
    try:
        world.write("pcas_call.py", CALL_FIXTURE)
        world.write("pcas_format.py", FORMAT_FIXTURE)
        report = PCAS.audit(world.path, SM)
        ok = True
        for name in ("pcas_call.py", "pcas_format.py"):
            row = row_of(report, name)
            ok = check(row.get("verdict") == PCAS.OUT_OF_SCOPE
                       and row.get("unresolved")
                       and not row.get("quieted"),
                       "AC-PCAS4 %s reads OUT-OF-SCOPE with the name "
                       "reported (%r)" % (name, (row.get("verdict"),
                                                 row.get("unresolved")))) \
                and ok
        shapes = PCAS.local_bindings(CALL_FIXTURE)
        ok = check(shapes.get("name") is None,
                   "AC-PCAS4 a call result is never a constant (%r)"
                   % (shapes,)) and ok
        got = PCAS.dynamic_imports(CALL_FIXTURE, world.path)
        ok = check(got is not None
                   and got["unresolved"] == ["importlib.import_module:name"],
                   "AC-PCAS4 the unresolved call is reported verbatim (%r)"
                   % (got,)) and ok
        names = PCAS._alias_pairs(CALL_FIXTURE, True)[1]
        ok = check(names.get("name") == PCAS.SHAPE_CALL,
                   "AC-PCAS4 the call is named as that shape (%r)"
                   % (names,)) and ok
        formats = PCAS._alias_pairs(FORMAT_FIXTURE, True)[1]
        ok = check(formats.get("name") == PCAS.SHAPE_EXPRESSION,
                   "AC-PCAS4 a percent format is named as an expression "
                   "(%r)" % (formats,)) and ok
        return ok
    finally:
        world.close()


def ac_pcas5():
    """The reading is read-only: no digest moves, no marker lands."""
    world = World(with_partial=True)
    try:
        world.write("pcas_alias_probe.py", CHAIN_FIXTURE)
        world.write("pcas_call.py", CALL_FIXTURE)
        before = dict((name, digest(os.path.join(world.path, name)))
                      for name in sorted(os.listdir(world.path)))
        module_before = digest(MODULE)
        render_before = digest(RENDER_MODULE)
        PCAS.audit(world.path, SM)
        PCAS.reading(world.path, SM)
        after = dict((name, digest(os.path.join(world.path, name)))
                     for name in sorted(os.listdir(world.path)))
        ok = check(before == after and not os.path.isfile(
            os.path.join(world.path, MARKER)),
            "AC-PCAS5 every fixture digest is unchanged and nothing landed")
        ok = check(digest(MODULE) == module_before
                   and digest(RENDER_MODULE) == render_before,
                   "AC-PCAS5 the shipped module and render are unchanged") \
            and ok
        refused = PCAS.reading(os.path.join(world.path, "no-such-root"), SM)
        ok = check(refused.get("refusal") == PCAS.E_NO_ROOT
                   and refused["verdict"] == PCAS.SEAMS_STALE,
                   "AC-PCAS5 a missing root is refused, not silently clean") \
            and ok
        return ok
    finally:
        world.close()


def ac_pcas6():
    """Pure ASCII, stdlib only, no clock, no network, wired once."""
    text = read_text(MODULE)
    suite = read_text(os.path.abspath(__file__))
    ok = check(all(ord(char) < 128 for char in text),
               "AC-PCAS6 the module source is pure ASCII")
    ok = check(all(ord(char) < 128 for char in suite),
               "AC-PCAS6 this suite source is pure ASCII") and ok
    imports = sorted(set(re.findall(r"(?m)^import ([A-Za-z_][A-Za-z0-9_]*)",
                                   text)))
    allowed = ("argparse", "ast", "hashlib", "json", "os", "re", "sys",
               "warnings")
    ok = check(not [name for name in imports if name not in allowed],
               "AC-PCAS6 only the allowed stdlib modules are imported (%s)"
               % (",".join(imports),)) and ok
    forbidden = ("time.time", "datetime", "socket", "urllib", "requests",
                 "http.client", "subprocess")
    ok = check(not [token for token in forbidden if token in text],
               "AC-PCAS6 no clock and no network token in the module") and ok
    registry = read_text(REGISTRY)
    ok = check(WIRED_LABEL in registry and WIRED_SUITE in registry,
               "AC-PCAS6 the face and its suite are wired into the registry "
               "exactly once") and ok
    ok = check(registry.count(WIRED_LABEL) == 1
               and registry.count(WIRED_SUITE) == 1,
               "AC-PCAS6 no duplicate registry row") and ok
    ok = check(PCAS.LABEL == "os-probe-seam-constant-alias-scope",
               "AC-PCAS6 the reconcile label is the face own (%s)"
               % PCAS.LABEL) and ok
    ok = check(PCAS.SEAMS_COVERED == "SEAMS-ALIAS-COVERED",
               "AC-PCAS6 the reading has its own verdict word (%s)"
               % PCAS.SEAMS_COVERED) and ok
    ok = check(PCAS._annotated_reader() is not PCAS._base_reader(),
               "AC-PCAS6 the extension asks the shipped faces, not a copy") \
        and ok
    returned = PCAS.resolve_expression('"%s"' % HELPER, CHAIN_FIXTURE)
    ok = check(isinstance(returned, tuple) and len(returned) == 2,
               "AC-PCAS6 the resolution answers a pair (%r)"
               % (returned,)) and ok
    return ok


def main():
    print("PROBE SEAM CONSTANT ALIAS SCOPE SUITE (AC-PCAS1..AC-PCAS6)")
    results = [ac_pcas1(), ac_pcas2(), ac_pcas3(), ac_pcas4(), ac_pcas5(),
               ac_pcas6()]
    passed = len([item for item in results if item])
    print("SUITE %s %d/%d criteria green"
          % ("PASS" if passed == EXPECTED_CRITERIA else "FAIL",
             passed, EXPECTED_CRITERIA))
    return 0 if passed == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())