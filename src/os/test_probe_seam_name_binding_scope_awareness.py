"""AC-PNSB1..AC-PNSB6 suite for the seam name-binding scope face (R2539).

Criteria were pinned in state/queue/tech.md:575 at R2537 BEFORE this code
existed.

What this proves: MEASURED at R2537 on the shipped nested-key face own readers,
`_bindings_of` walks the WHOLE module, so one name bound in two different
function bodies merges into a single table and reads ambiguous even though each
scope is unambiguous on its own, and a function-local name leaks into a
module-level loop it cannot reach. This face resolves a NAME step against the
binding table of the SCOPE the loop is in and publishes which scope it
followed.

Every fixture lives in a private temporary directory or in a string; no shipped
source file is written.

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

import probe_seam_name_binding_scope_awareness as PNSB  # noqa: E402
import probe_seam_nested_key_binding_scope as PNKB  # noqa: E402
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "probe_seam_name_binding_scope_awareness.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
BASE_MODULE = os.path.join(BASE, "probe_seam_nested_key_binding_scope.py")
RENDER_MODULE = os.path.join(SANDBOX, "suite_matrix.py")
WIRED_LABEL = '"os-probe-seam-name-binding-scope-awareness",'
WIRED_SUITE = '"test_probe_seam_name_binding_scope_awareness.py"), 6),'

HELPER = "pnsb_helper"

FUNCTION_LOCAL_FIXTURE = ('D = {"a": {"b": ("%s",)}}\n'
                          '\n'
                          'def run():\n'
                          '    KEY = "b"\n'
                          '    for name in D["a"][KEY]:\n'
                          '        pass\n' % HELPER)

SIBLING_FIXTURE = ('D = {"a": {"b": ("%s",)}}\n'
                   '\n'
                   'def first():\n'
                   '    KEY = "b"\n'
                   '    for name in D["a"][KEY]:\n'
                   '        pass\n'
                   '\n'
                   'def second():\n'
                   '    KEY = "zzz"\n'
                   '    for name in D["a"][KEY]:\n'
                   '        pass\n' % HELPER)

MODULE_VISIBLE_FIXTURE = ('D = {"a": {"b": ("%s",)}}\n'
                          'KEY = "b"\n'
                          '\n'
                          'def run():\n'
                          '    for name in D["a"][KEY]:\n'
                          '        pass\n' % HELPER)

SHADOWED_FIXTURE = ('D = {"a": {"b": ("%s",), "c": ("%s",)}}\n'
                    'KEY = "b"\n'
                    '\n'
                    'def run():\n'
                    '    KEY = "c"\n'
                    '    for name in D["a"][KEY]:\n'
                    '        pass\n' % (HELPER, HELPER))

TWICE_LOCAL_FIXTURE = ('D = {"a": {"b": ("%s",)}}\n'
                       '\n'
                       'def run():\n'
                       '    KEY = "b"\n'
                       '    KEY = "zzz"\n'
                       '    for name in D["a"][KEY]:\n'
                       '        pass\n' % HELPER)

TWICE_MODULE_FIXTURE = ('D = {"a": {"b": ("%s",)}}\n'
                        'KEY = "b"\n'
                        'KEY = "zzz"\n'
                        '\n'
                        'for name in D["a"][KEY]:\n'
                        '    pass\n' % HELPER)

PROBE_FIXTURE = ('import importlib\n'
                 '\n'
                 'D = {"a": {"b": ("%s",)}}\n'
                 '\n'
                 'def run():\n'
                 '    KEY = "b"\n'
                 '    for name in D["a"][KEY]:\n'
                 '        return importlib.import_module(name).QUIETED\n'
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


def helper_text(seams):
    return 'QUIETED = (%s,)\n' % ", ".join('"%s"' % name for name in seams)


def loop_rows(text):
    return PNSB.scope_report(text)["loops"]


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
    """A private root holding one quieting helper and one probe."""

    def __init__(self):
        self.path = tempfile.mkdtemp(prefix="pnsb-suite-")
        seams = PNSB.seam_names(SM)
        write_ascii(os.path.join(self.path, HELPER + ".py"),
                    helper_text(seams))

    def write(self, name, text):
        write_ascii(os.path.join(self.path, name), text)
        return name

    def close(self):
        shutil.rmtree(self.path, ignore_errors=True)


def ac_pnsb1():
    """A name bound only inside the enclosing function resolves there."""
    tables = PNSB.scope_tables(FUNCTION_LOCAL_FIXTURE)
    ok = check(tables is not None
               and "KEY" in tables["functions"]["run"]
               and "KEY" not in tables["module"],
               "AC-PNSB1 the function own table holds KEY and the module "
               "table does not (%r)" % (tables,))
    got = PNSB.scoped_entry("KEY", FUNCTION_LOCAL_FIXTURE, "function:run")
    ok = check(got["state"] == "ok" and got["value"] == "b"
               and got["scope"] == "function:run" and not got["shadow"],
               "AC-PNSB1 the loop scope resolves to the function binding "
               "(%r)" % (got,)) and ok
    rows = loop_rows(FUNCTION_LOCAL_FIXTURE)
    ok = check(len(rows) == 1 and rows[0]["scope"] == "function:run"
               and rows[0]["followed"].get("KEY") == "b"
               and rows[0]["refused"] == {},
               "AC-PNSB1 the loop row names its scope and follows the value "
               "(%r)" % (rows,)) and ok
    ok = check(rows[0]["taken_from"].get("KEY") == "function:run",
               "AC-PNSB1 and it publishes where the value was taken from "
               "(%r)" % (rows[0]["taken_from"],)) and ok
    return ok


def ac_pnsb2():
    """A sibling function binding the same name does not make it ambiguous."""
    rows = loop_rows(SIBLING_FIXTURE)
    ok = check(len(rows) == 2,
               "AC-PNSB2 both loops are read (%r)" % (rows,))
    first = [row for row in rows if row["scope"] == "function:first"]
    second = [row for row in rows if row["scope"] == "function:second"]
    ok = check(len(first) == 1 and first[0]["followed"].get("KEY") == "b"
               and first[0]["refused"] == {},
               "AC-PNSB2 the first function own loop follows its own "
               "constant (%r)" % (first,)) and ok
    ok = check(len(second) == 1
               and second[0]["followed"].get("KEY") == "zzz"
               and second[0]["refused"] == {},
               "AC-PNSB2 the sibling loop follows ITS constant, not the "
               "first one (%r)" % (second,)) and ok
    got = PNSB.scoped_entry("KEY", SIBLING_FIXTURE, "function:first")
    ok = check(got["state"] == "ok" and got["value"] == "b",
               "AC-PNSB2 the sibling binding is not merged into one "
               "ambiguous table (%r)" % (got,)) and ok
    return ok


def ac_pnsb3():
    """A module name reaches a function loop unless the function shadows it."""
    got = PNSB.scoped_entry("KEY", MODULE_VISIBLE_FIXTURE, "function:run")
    ok = check(got["state"] == "ok" and got["value"] == "b"
               and got["scope"] == "module" and not got["shadow"],
               "AC-PNSB3 an unshadowed module name is visible to the "
               "function loop (%r)" % (got,))
    rows = loop_rows(MODULE_VISIBLE_FIXTURE)
    ok = check(rows and rows[0]["followed"].get("KEY") == "b"
               and rows[0]["taken_from"].get("KEY") == "module"
               and rows[0]["shadowed"] == [],
               "AC-PNSB3 the row names the module as the source (%r)"
               % (rows,)) and ok
    got = PNSB.scoped_entry("KEY", SHADOWED_FIXTURE, "function:run")
    ok = check(got["state"] == "ok" and got["value"] == "c"
               and got["scope"] == "function:run" and got["shadow"],
               "AC-PNSB3 a shadowing function resolves to the inner binding "
               "and announces the shadow (%r)" % (got,)) and ok
    rows = loop_rows(SHADOWED_FIXTURE)
    ok = check(rows and rows[0]["followed"].get("KEY") == "c"
               and rows[0]["shadowed"] == ["KEY"],
               "AC-PNSB3 the loop row carries the shadow (%r)" % (rows,)) and ok
    got = PNSB.scoped_entry("KEY", MODULE_VISIBLE_FIXTURE, "module")
    ok = check(got["state"] == "ok" and got["scope"] == "module"
               and not got["shadow"],
               "AC-PNSB3 a module-level loop reads the module table (%r)"
               % (got,)) and ok
    return ok


def ac_pnsb4():
    """A name bound twice INSIDE one scope stays ambiguous at its hop."""
    got = PNSB.scoped_entry("KEY", TWICE_LOCAL_FIXTURE, "function:run")
    ok = check(got["state"] == "refused"
               and got["reason"] == PNSB.REFUSED_AMBIGUOUS,
               "AC-PNSB4 a twice-bound function name is refused as ambiguous "
               "(%r)" % (got,))
    rows = loop_rows(TWICE_LOCAL_FIXTURE)
    ok = check(rows and rows[0]["refused"].get("KEY") == "ambiguous"
               and rows[0]["followed"] == {},
               "AC-PNSB4 the loop row NAMES the ambiguity rather than "
               "picking one (%r)" % (rows,)) and ok
    got = PNSB.scoped_entry("KEY", TWICE_MODULE_FIXTURE, "module")
    ok = check(got["state"] == "refused"
               and got["reason"] == PNSB.REFUSED_AMBIGUOUS,
               "AC-PNSB4 the module scope refuses the same shape (%r)"
               % (got,)) and ok
    got = PNSB.scoped_entry("KEY", TWICE_LOCAL_FIXTURE, "function:first")
    ok = check(got["state"] == "refused",
               "AC-PNSB4 a scope with no binding does not borrow another "
               "scope own constants (%r)" % (got,)) and ok
    return ok


def ac_pnsb5():
    """The reading is read-only: no digest moves across a full audit."""
    world = World()
    try:
        world.write("pnsb_probe.py", PROBE_FIXTURE)
        before = tree_digest(world.path)
        module_before = digest(MODULE)
        base_before = digest(BASE_MODULE)
        render_before = digest(RENDER_MODULE)
        report = PNSB.audit(world.path, SM)
        ok = check(tree_digest(world.path) == before,
                   "AC-PNSB5 the probed tree is byte-identical after the "
                   "audit")
        ok = check(digest(MODULE) == module_before
                   and digest(BASE_MODULE) == base_before
                   and digest(RENDER_MODULE) == render_before,
                   "AC-PNSB5 the reading moved no shipped digest") and ok
        row = row_of(report, "pnsb_probe.py")
        ok = check(row.get("verdict") == PNSB.COVERED,
                   "AC-PNSB5 the probe row still reads COVERED (%r)"
                   % (row.get("verdict"),)) and ok
        ok = check(row.get("scope_loops")
                   and row["scope_loops"][0]["followed"].get("KEY") == "b",
                   "AC-PNSB5 the row carries this face own scope loop (%r)"
                   % (row.get("scope_loops"),)) and ok
        ok = check(report["tool"] == PNSB.LABEL
                   and report["verdict"] == PNSB.SEAMS_COVERED
                   and report["base_tool"] == PNKB.LABEL,
                   "AC-PNSB5 the report keeps the shipped base label and "
                   "answers its own (%r)"
                   % ((report["tool"], report["verdict"],
                       report.get("base_tool")),)) and ok
        refusal = PNSB.reading(os.path.join(world.path, "absent"), SM)
        ok = check(refusal.get("refusal") == PNSB.E_NO_ROOT
                   and refusal.get("probes") == [],
                   "AC-PNSB5 a missing root is refused, not raised (%r)"
                   % (refusal.get("refusal"),)) and ok
    finally:
        world.close()
    return ok


def ac_pnsb6():
    """Pure ASCII, stdlib only, no clock, no network, wired once."""
    text = read_text(MODULE)
    suite = read_text(os.path.abspath(__file__))
    ok = check(all(ord(char) < 128 for char in text),
               "AC-PNSB6 the module source is pure ASCII")
    ok = check(all(ord(char) < 128 for char in suite),
               "AC-PNSB6 this suite source is pure ASCII") and ok
    imports = sorted(set(re.findall(r"(?m)^import ([A-Za-z_][A-Za-z0-9_]*)",
                                    text)))
    allowed = ("argparse", "ast", "hashlib", "json", "os", "re", "sys")
    ok = check(not [name for name in imports if name not in allowed],
               "AC-PNSB6 only the allowed stdlib modules are imported (%s)"
               % (",".join(imports),)) and ok
    forbidden = ("time.time", "datetime", "socket", "urllib", "requests",
                 "http.client", "subprocess")
    ok = check(not [token for token in forbidden if token in text],
               "AC-PNSB6 no clock and no network token in the module") and ok
    registry = read_text(REGISTRY)
    ok = check(WIRED_LABEL in registry and WIRED_SUITE in registry,
               "AC-PNSB6 the face and its suite are wired into the registry "
               "exactly once") and ok
    ok = check(registry.count(WIRED_LABEL) == 1
               and registry.count(WIRED_SUITE) == 1,
               "AC-PNSB6 no duplicate registry row") and ok
    ok = check(PNSB.LABEL == "os-probe-seam-name-binding-scope-awareness",
               "AC-PNSB6 the reconcile label is the face own (%s)"
               % PNSB.LABEL) and ok
    ok = check(PNSB.SEAMS_COVERED == "SEAMS-NAME-SCOPE-COVERED"
               and PNSB.SEAMS_STALE == "SEAMS-NAME-SCOPE-STALE",
               "AC-PNSB6 the reading has its own verdict words (%s/%s)"
               % (PNSB.SEAMS_COVERED, PNSB.SEAMS_STALE)) and ok
    ok = check(PNKB.LABEL == "os-probe-seam-nested-key-binding-scope",
               "AC-PNSB6 the shipped face it extends is still named") and ok
    return ok


def main():
    print("PROBE SEAM NAME BINDING SCOPE SUITE (AC-PNSB1..AC-PNSB6)")
    results = [ac_pnsb1(), ac_pnsb2(), ac_pnsb3(), ac_pnsb4(), ac_pnsb5(),
               ac_pnsb6()]
    passed = len([item for item in results if item])
    print("SUITE %s %d/%d criteria green"
          % ("PASS" if passed == EXPECTED_CRITERIA else "FAIL",
             passed, EXPECTED_CRITERIA))
    return 0 if passed == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())