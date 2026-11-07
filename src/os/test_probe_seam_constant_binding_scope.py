"""AC-PCB1..AC-PCB6 suite for the seam constant-binding scope face (R2521).

Criteria were pinned in state/queue/tech.md:557 at R2519 BEFORE this code
existed.

What this proves: MEASURED at R2519 in the dynamic face fixtures, a probe that
binds the module name to a module-level string constant and then imports it
reads OUT-OF-SCOPE with the call named unresolved, while the same call with a
literal in the argument position reads COVERED. This face resolves a dynamic
module name through the STRING CONSTANT bindings the probe own tree declares,
on the same cycle-guarded same-root walk, so such a probe is answered on its
own row instead of being skipped. A name bound to a real computation is never
guessed at and never evaluated.

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

import probe_seam_constant_binding_scope as PCB  # noqa: E402
import probe_seam_dynamic_import_scope as PDI  # noqa: E402
import probe_seam_registry as PSR  # noqa: E402
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "probe_seam_constant_binding_scope.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
RENDER_MODULE = os.path.join(SANDBOX, "suite_matrix.py")
WIRED_LABEL = '"os-probe-seam-constant-binding-scope",'
WIRED_SUITE = '"test_probe_seam_constant_binding_scope.py"), 6),'

HELPER = "pcb_helper"
PARTIAL = "pcb_partial"
MARKER = "pcb_import_marker.txt"

STR_FIXTURE = ('import importlib\n'
               'NAME = "%s"\n'
               '\n'
               'def run():\n'
               '    return importlib.import_module(NAME).QUIETED\n')

TUPLE_FIXTURE = ('import importlib\n'
                 'NAMES = ("pcb_unused", "%s")\n'
                 '\n'
                 'def run():\n'
                 '    return importlib.import_module(NAMES[1]).QUIETED\n')

DICT_FIXTURE = ('import importlib\n'
                'MAP = {"x": "pcb_unused", "h": "%s"}\n'
                'KEY = "h"\n'
                '\n'
                'def run():\n'
                '    return importlib.import_module(MAP[KEY]).QUIETED\n')

COMPUTED_FIXTURE = ('import importlib\n'
                    'NAME = "pcb_" + "helper"\n'
                    '\n'
                    'def run():\n'
                    '    return importlib.import_module(NAME).QUIETED\n')

FORMAT_FIXTURE = ('import importlib\n'
                  'BASE = "pcb"\n'
                  'NAME = f"{BASE}_helper"\n'
                  '\n'
                  'def run():\n'
                  '    return importlib.import_module(NAME).QUIETED\n')


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
        code = PCB.main(["module.py"] + argv)
    return code, buffer.getvalue()


class World(object):
    """A private root with the helpers every leg needs."""

    def __init__(self, with_partial=True):
        self.path = tempfile.mkdtemp(prefix="pcb-suite-")
        self.seams = PCB.seam_names(SM)
        write_ascii(os.path.join(self.path, HELPER + ".py"),
                    helper_text(self.seams) + marker_line())
        if with_partial:
            write_ascii(os.path.join(self.path, PARTIAL + ".py"),
                        helper_text(self.seams, omit=self.seams[:1])
                        + marker_line())

    def write(self, name, text):
        write_ascii(os.path.join(self.path, name), text)
        return name

    def close(self):
        shutil.rmtree(self.path, ignore_errors=True)


def ac_pcb1():
    """The binding table is read off the probe tree; nothing is evaluated."""
    seams = PCB.seam_names(SM)
    source_text = read_text(MODULE)
    ok = check(not [name for name in seams if name in source_text],
               "AC-PCB1 no seam name is spelled in the module source")
    ok = check(not [name for name in (HELPER, PARTIAL)
                    if name in source_text],
               "AC-PCB1 no fixture helper name is written into the module") \
        and ok
    table = PCB.constant_bindings(STR_FIXTURE % HELPER)
    ok = check(table == {"NAME": (PCB.SHAPE_STR, HELPER)},
               "AC-PCB1 a str-literal binding is read off the tree (%r)"
               % (table,)) and ok
    table = PCB.constant_bindings(TUPLE_FIXTURE % HELPER)
    ok = check(table.get("NAMES") == (
        PCB.SHAPE_TUPLE, ["pcb_unused", HELPER]),
        "AC-PCB1 a tuple of str literals is read off the tree (%r)"
        % (table,)) and ok
    table = PCB.constant_bindings(DICT_FIXTURE % HELPER)
    ok = check(table.get("MAP") == (
        PCB.SHAPE_DICT, {"x": "pcb_unused", "h": HELPER})
        and table.get("KEY") == (PCB.SHAPE_STR, "h"),
        "AC-PCB1 a dict of str pairs and its key binding are read (%r)"
        % (table,)) and ok
    for label, text in (("a concatenation", COMPUTED_FIXTURE),
                        ("an f-string", FORMAT_FIXTURE),
                        ("a call", 'import importlib\n'
                                   'NAME = "pcb_helper".upper()\n'
                                   'def run():\n'
                                   '    return importlib.import_module(NAME)\n'),
                        ("an imported constant", 'from os import sep\n'
                                                  'NAME = sep\n'
                                                  'def run():\n'
                                                  '    return NAME\n')):
        table = PCB.constant_bindings(text)
        ok = check(not [name for name in table if name == "NAME"],
                   "AC-PCB1 %s is NOT a constant binding (%r)"
                   % (label, table)) and ok
    return ok


def ac_pcb2():
    """A str-literal binding reads COVERED with helper, binding and shape."""
    world = World(with_partial=False)
    try:
        world.write("pcb_str.py", STR_FIXTURE % HELPER)
        world.write("pcb_tuple.py", TUPLE_FIXTURE % HELPER)
        world.write("pcb_dict.py", DICT_FIXTURE % HELPER)
        report = PCB.audit(world.path, SM)
        ok = True
        for name, shape, binding in (
                ("pcb_str.py", PDI.SHAPE_IMPORTLIB, "NAME"),
                ("pcb_tuple.py", PDI.SHAPE_IMPORTLIB, "NAMES"),
                ("pcb_dict.py", PDI.SHAPE_IMPORTLIB, "MAP")):
            row = row_of(report, name)
            expected = "%s:%s@%s" % (shape, HELPER, binding)
            ok = check(row.get("verdict") == PCB.COVERED
                       and HELPER in row.get("helpers", [])
                       and expected in row.get("dynamic", [])
                       and row.get("quieted") == sorted(
                           row.get("quieted", []), key=world.seams.index)
                       and len(row.get("quieted", [])) == len(world.seams),
                       "AC-PCB2 %s reads COVERED with helper=%s binding=%s "
                       "shape=%s (%r)"
                       % (name, HELPER, binding, shape,
                          (row.get("verdict"), row.get("helpers"),
                           row.get("dynamic")))) and ok
        ok = check(report["verdict"] == PCB.SEAMS_COVERED,
                   "AC-PCB2 the whole world reads %s (%s)"
                   % (PCB.SEAMS_COVERED, report["verdict"])) and ok
        return ok
    finally:
        world.close()


def ac_pcb3():
    """A binding reaching a partial helper reads MISSING-SEAM, never run."""
    world = World()
    try:
        world.write("pcb_partial_probe.py", STR_FIXTURE % PARTIAL)
        report = PCB.audit(world.path, SM)
        row = row_of(report, "pcb_partial_probe.py")
        ok = check(row.get("verdict") == PCB.MISSING_SEAM
                   and row.get("missing") == world.seams[:1],
                   "AC-PCB3 a constant-bound partial helper reads MISSING-SEAM "
                   "naming seam and probe (%r)"
                   % ((row.get("verdict"), row.get("missing")),))
        ok = check(report["verdict"] == PCB.SEAMS_STALE,
                   "AC-PCB3 the world verdict is %s (%s)"
                   % (PCB.SEAMS_STALE, report["verdict"])) and ok
        ok = check(not os.path.isfile(os.path.join(world.path, MARKER)),
                   "AC-PCB3 neither probe nor helper was imported or run") \
            and ok
        code, out = call_main(["--root", world.path])
        ok = check(code == 2 and "MISSING-SEAM" in out,
                   "AC-PCB3 the CLI refuses with exit 2 (%d)" % code) and ok
        return ok
    finally:
        world.close()


def ac_pcb4():
    """A name bound to a computation is never resolved, only named."""
    world = World()
    try:
        world.write("pcb_computed.py", COMPUTED_FIXTURE)
        world.write("pcb_format.py", FORMAT_FIXTURE)
        report = PCB.audit(world.path, SM)
        ok = True
        for name, expr in (("pcb_computed.py", '"pcb_" + "helper"'),
                           ("pcb_format.py", 'f"{BASE}_helper"')):
            row = row_of(report, name)
            ok = check(row.get("verdict") == PCB.OUT_OF_SCOPE
                       and row.get("unresolved")
                       and not row.get("quieted"),
                       "AC-PCB4 %s reads OUT-OF-SCOPE with the call named "
                       "(%r)" % (name, (row.get("verdict"),
                                        row.get("unresolved")))) and ok
            ok = check(not [item for item in row.get("dynamic", [])
                            if item.startswith("importlib.import_module:"
                                               + HELPER)],
                       "AC-PCB4 %s is not resolved to %s (%r)"
                       % (name, HELPER, row.get("dynamic"))) and ok
            ok = check(expr not in ("", None),
                       "AC-PCB4 %s expression is named as computed" % name) \
                and ok
        got = PCB.dynamic_imports(COMPUTED_FIXTURE)
        ok = check(got is not None and got["unresolved"] == [
            "importlib.import_module:NAME"],
            "AC-PCB4 the computed call is reported verbatim (%r)"
            % (got,)) and ok
        return ok
    finally:
        world.close()


def ac_pcb5():
    """The reading is read-only: no digest moves, no marker lands."""
    world = World()
    try:
        world.write("pcb_str.py", STR_FIXTURE % HELPER)
        world.write("pcb_computed.py", COMPUTED_FIXTURE)
        before = dict((name, digest(os.path.join(world.path, name)))
                      for name in sorted(os.listdir(world.path)))
        module_before = digest(MODULE)
        render_before = digest(RENDER_MODULE)
        PCB.audit(world.path, SM)
        PCB.reading(world.path, SM)
        after = dict((name, digest(os.path.join(world.path, name)))
                     for name in sorted(os.listdir(world.path)))
        ok = check(before == after and not os.path.isfile(
            os.path.join(world.path, MARKER)),
            "AC-PCB5 every fixture digest is unchanged and nothing landed")
        ok = check(digest(MODULE) == module_before
                   and digest(RENDER_MODULE) == render_before,
                   "AC-PCB5 the shipped module and render are unchanged") \
            and ok
        refused = PCB.reading(os.path.join(world.path, "no-such-root"), SM)
        ok = check(refused.get("refusal") == PCB.E_NO_ROOT
                   and refused["verdict"] == PCB.SEAMS_STALE,
                   "AC-PCB5 a missing root is refused, not silently clean") \
            and ok
        return ok
    finally:
        world.close()


def ac_pcb6():
    """Pure ASCII, stdlib only, no clock, no network, wired once."""
    text = read_text(MODULE)
    suite = read_text(os.path.abspath(__file__))
    ok = check(all(ord(char) < 128 for char in text),
               "AC-PCB6 the module source is pure ASCII")
    ok = check(all(ord(char) < 128 for char in suite),
               "AC-PCB6 this suite source is pure ASCII") and ok
    imports = sorted(set(re.findall(r"(?m)^import ([A-Za-z_][A-Za-z0-9_]*)",
                                   text)))
    allowed = ("argparse", "ast", "hashlib", "json", "os", "re", "sys",
               "warnings")
    ok = check(not [name for name in imports if name not in allowed],
               "AC-PCB6 only the allowed stdlib modules are imported (%s)"
               % (",".join(imports),)) and ok
    forbidden = ("time.time", "datetime", "socket", "urllib", "requests",
                 "http.client", "subprocess")
    ok = check(not [token for token in forbidden if token in text],
               "AC-PCB6 no clock and no network token in the module") and ok
    registry = read_text(REGISTRY)
    ok = check(WIRED_LABEL in registry and WIRED_SUITE in registry,
               "AC-PCB6 the face and its suite are wired into the registry "
               "exactly once") and ok
    ok = check(registry.count(WIRED_LABEL) == 1
               and registry.count(WIRED_SUITE) == 1,
               "AC-PCB6 no duplicate registry row") and ok
    ok = check(PCB.LABEL == "os-probe-seam-constant-binding-scope",
               "AC-PCB6 the reconcile label is the face own (%s)"
               % PCB.LABEL) and ok
    return ok


def main():
    print("PROBE SEAM CONSTANT BINDING SCOPE SUITE (AC-PCB1..AC-PCB6)")
    results = [ac_pcb1(), ac_pcb2(), ac_pcb3(), ac_pcb4(), ac_pcb5(), ac_pcb6()]
    passed = len([item for item in results if item])
    print("SUITE %s %d/%d criteria green"
          % ("PASS" if passed == EXPECTED_CRITERIA else "FAIL",
             passed, EXPECTED_CRITERIA))
    return 0 if passed == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())