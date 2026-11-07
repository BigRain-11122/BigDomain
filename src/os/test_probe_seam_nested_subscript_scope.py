"""AC-PCNS1..AC-PCNS6 suite for the seam nested-subscript scope face (R2535).

Criteria were pinned in state/queue/tech.md:571 at R2533 BEFORE this code
existed.

What this proves: MEASURED at R2533 on the shipped subscript face own readers,
a for-loop over a CHAIN of two constant subscripts read refused=nested and
named NO key at all, even though the outer and the inner container were both
literal constants - so an operator was told nothing about which step broke.
This face follows a chain of constant subscripts on a literal container
(module body and function bodies), resolves it only when the result holds
EXACTLY ONE element and carries the chain with EVERY key, and NAMES every
shape it refuses together with the HOP that broke - including an integer index
into a tuple, which is never followed.

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

import probe_seam_nested_subscript_scope as PCNS  # noqa: E402
import probe_seam_subscript_container_scope as PCSC  # noqa: E402
import probe_seam_for_container_name as PCFN  # noqa: E402
import probe_seam_dynamic_import_scope as PDI  # noqa: E402
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "probe_seam_nested_subscript_scope.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
RENDER_MODULE = os.path.join(SANDBOX, "suite_matrix.py")
WIRED_LABEL = '"os-probe-seam-nested-subscript-scope",'
WIRED_SUITE = '"test_probe_seam_nested_subscript_scope.py"), 6),'

HELPER = "pcns_helper"
PARTIAL = "pcns_partial"
PKG = "pcns_pkg"
MARKER = "pcns_marker.txt"

NEST_FIXTURE = ('import importlib\n'
                '\n'
                'D = {"a": {"b": ("%s",)}}\n'
                '\n'
                'for name in D["a"]["b"]:\n'
                '    importlib.import_module(name)\n' % HELPER)

NEST_LOCAL_FIXTURE = ('import importlib\n'
                      '\n'
                      'D = {"a": {"b": ("%s",)}}\n'
                      '\n'
                      'def run():\n'
                      '    for name in D["a"]["b"]:\n'
                      '        return importlib.import_module(name).QUIETED\n'
                      % HELPER)

CHAIN_FIXTURE = ('import importlib\n'
                 'import %s\n'
                 '\n'
                 'for name in %s.GROUPS["a"]["b"]:\n'
                 '    importlib.import_module(name)\n' % (PKG, PKG))

CHAIN_BROKEN_FIXTURE = ('import %s\n'
                        '\n'
                        'for name in %s.MISSING["a"]["b"]:\n'
                        '    pass\n' % (PKG, PKG))

KEY_MISSING_FIXTURE = ('D = {"a": {"b": ("%s",)}}\n'
                       '\n'
                       'for name in D["a"]["zzz"]:\n'
                       '    pass\n' % HELPER)

INDEX_FIXTURE = ('D = {"a": ("%s",)}\n'
                 '\n'
                 'for name in D["a"][0]:\n'
                 '    pass\n' % HELPER)

NONCONST_FIXTURE = ('D = {"a": {"b": ("%s",)}}\n'
                    'KEY = "b"\n'
                    '\n'
                    'for name in D["a"][KEY]:\n'
                    '    pass\n' % HELPER)

MULTI_ELEMENT_FIXTURE = ('D = {"a": {"b": ("pcns_unused", "%s")}}\n'
                         '\n'
                         'for name in D["a"]["b"]:\n'
                         '    pass\n' % HELPER)

CALL_FIXTURE = ('open("%s", "w", encoding="ascii").write("ran\\n")\n'
                '\n'
                'D = {"a": {"b": ("%s",)}}\n'
                '\n'
                'def pick():\n'
                '    return D\n'
                '\n'
                'for name in pick()["a"]["b"]:\n'
                '    pass\n' % (MARKER, HELPER))

FORMAT_FIXTURE = ('D = {"a": {"b": ("%s",)}}\n'
                  '\n'
                  'for name in D["a"]["{}".format("b")]:\n'
                  '    pass\n' % HELPER)

COMPREHENSION_FIXTURE = ('for name in [item for item in ("pcns_helper",)]'
                         '["a"]["b"]:\n'
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
        self.path = tempfile.mkdtemp(prefix="pcns-suite-")
        self.seams = PCNS.seam_names(SM)
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


def ac_pcns1():
    """A two-key chain of a literal container resolves with BOTH keys."""
    table = PCNS.module_bindings(NEST_FIXTURE)
    ok = check(table.get("name") == (PCNS.TREE_STR, HELPER),
               "AC-PCNS1 a module-level two-key chain resolves (%r)"
               % (table,))
    local = PCNS.local_bindings(NEST_LOCAL_FIXTURE)
    ok = check(local.get("name") == (PCNS.TREE_STR, HELPER),
               "AC-PCNS1 a function-body two-key chain resolves (%r)"
               % (local,)) and ok
    report = PCNS.nested_report(NEST_FIXTURE)
    ok = check(report.get("followed", {}).get("name")
               == "nsub:name@D['a']['b']",
               "AC-PCNS1 the chain carries BOTH keys (%r)" % (report,)) and ok
    report = PCNS.nested_report(NEST_LOCAL_FIXTURE)
    ok = check(report.get("followed", {}).get("name")
               == "nsub:name@D['a']['b']",
               "AC-PCNS1 the local chain carries both keys too (%r)"
               % (report,)) and ok
    world = World(with_partial=False)
    try:
        world.write("pcns_probe.py", NEST_LOCAL_FIXTURE)
        report = PCNS.audit(world.path, SM)
        row = row_of(report, "pcns_probe.py")
        expected = "%s:%s@name" % (PDI.SHAPE_IMPORTLIB, HELPER)
        ok = check(row.get("verdict") == PCNS.COVERED
                   and expected in row.get("dynamic", []),
                   "AC-PCNS1 the probe row reads COVERED and names the "
                   "chain binding (%r)"
                   % ((row.get("verdict"), row.get("dynamic")),)) and ok
        ok = check(row.get("containers") == ["l:name@nsub:name@D['a']['b']"],
                   "AC-PCNS1 the row carries the chain with both keys (%r)"
                   % (row.get("containers"),)) and ok
    finally:
        world.close()
    return ok


def ac_pcns2():
    """A missing second key, an index step or a broken hop is NAMED by hop."""
    world = World(with_partial=False)
    try:
        table = PCNS.module_bindings(CHAIN_FIXTURE, world.path)
        ok = check(table.get("name") == (PCNS.TREE_STR, HELPER),
                   "AC-PCNS2 a same-root chained subscript resolves (%r)"
                   % (table,))
        report = PCNS.nested_report(CHAIN_FIXTURE, world.path)
        ok = check(report.get("followed", {}).get("name")
                   == "nsub:name@%s.GROUPS['a']['b']" % PKG,
                   "AC-PCNS2 the chained label carries both keys (%r)"
                   % (report,)) and ok
        report = PCNS.nested_report(KEY_MISSING_FIXTURE, world.path)
        reason = report.get("refused", {}).get("name") or ""
        ok = check(reason.startswith("key@hop2:")
                   and "'zzz'" in reason,
                   "AC-PCNS2 a missing second key is NAMED with its hop (%r)"
                   % (report,)) and ok
        ok = check(reason != "nested",
                   "AC-PCNS2 and the refusal is not a bare shape word (%r)"
                   % (reason,)) and ok
        report = PCNS.nested_report(INDEX_FIXTURE, world.path)
        reason = report.get("refused", {}).get("name") or ""
        ok = check(reason.startswith("index@hop2:"),
                   "AC-PCNS2 an index into a tuple is NAMED at its hop, "
                   "never followed (%r)" % (report,)) and ok
        ok = check(PCNS.module_bindings(INDEX_FIXTURE, world.path) == {},
                   "AC-PCNS2 and an index step enters no table (%r)"
                   % (PCNS.module_bindings(INDEX_FIXTURE, world.path),)) and ok
        report = PCNS.nested_report(CHAIN_BROKEN_FIXTURE, world.path)
        reason = report.get("refused", {}).get("name") or ""
        ok = check(reason.startswith("attribute:") and "MISSING" in reason,
                   "AC-PCNS2 a broken same-root hop is NAMED (%r)"
                   % (report,)) and ok
        report = PCNS.nested_report(NONCONST_FIXTURE, world.path)
        reason = report.get("refused", {}).get("name") or ""
        ok = check(reason.startswith("key@hop2:") and "KEY" in reason,
                   "AC-PCNS2 a non-constant second step is NAMED, never "
                   "guessed (%r)" % (report,)) and ok
    finally:
        world.close()
    return ok


def ac_pcns3():
    """A multi-element two-deep result is NAMED ambiguous, never the first."""
    table = PCNS.module_bindings(MULTI_ELEMENT_FIXTURE)
    ok = check("name" not in table,
               "AC-PCNS3 a two-element result never enters the table (%r)"
               % (table,))
    report = PCNS.nested_report(MULTI_ELEMENT_FIXTURE)
    ok = check(report.get("refused", {}).get("name") == "ambiguous",
               "AC-PCNS3 the shape is NAMED ambiguous (%r)" % (report,)) and ok
    ok = check(report.get("followed", {}).get("name") is None,
               "AC-PCNS3 and nothing is published as followed (%r)"
               % (report,)) and ok
    ok = check(PCNS.module_bindings(MULTI_ELEMENT_FIXTURE).get("name")
               != (PCNS.TREE_STR, "pcns_unused"),
               "AC-PCNS3 the first element is never taken as the answer") and ok
    return ok


def ac_pcns4():
    """A call, a format and a comprehension step is NAMED, never evaluated."""
    world = World(with_partial=False)
    try:
        marker = os.path.join(world.path, MARKER)
        report = PCNS.nested_report(CALL_FIXTURE, world.path)
        reason = report.get("refused", {}).get("name") or ""
        ok = check(reason.startswith("call@hop1:")
                   or reason.startswith("call@hop2:"),
                   "AC-PCNS4 a call base is NAMED call with its hop (%r)"
                   % (report,))
        ok = check(not os.path.exists(marker),
                   "AC-PCNS4 nothing was evaluated (marker absent)") and ok
        ok = check(PCNS.module_bindings(CALL_FIXTURE, world.path) == {},
                   "AC-PCNS4 and a call base enters no table") and ok
        report = PCNS.nested_report(FORMAT_FIXTURE, world.path)
        reason = report.get("refused", {}).get("name") or ""
        ok = check(reason.startswith("format@hop2:"),
                   "AC-PCNS4 a format step is NAMED format at its hop (%r)"
                   % (report,)) and ok
        ok = check(PCNS.module_bindings(FORMAT_FIXTURE, world.path) == {},
                   "AC-PCNS4 and a format step enters no table") and ok
        report = PCNS.nested_report(COMPREHENSION_FIXTURE, world.path)
        reason = report.get("refused", {}).get("name") or ""
        ok = check(reason.startswith("comprehension@hop1:"),
                   "AC-PCNS4 a comprehension base is NAMED comprehension (%r)"
                   % (report,)) and ok
    finally:
        world.close()
    return ok


def ac_pcns5():
    """The reading is read-only: no digest moves across a full audit."""
    world = World(with_partial=False)
    try:
        world.write("pcns_good_probe.py", NEST_FIXTURE)
        world.write("pcns_bad_probe.py", CHAIN_BROKEN_FIXTURE)
        before = tree_digest(world.path)
        module_before = digest(MODULE)
        base_before = digest(os.path.join(
            BASE, "probe_seam_subscript_container_scope.py"))
        render_before = digest(RENDER_MODULE)
        report = PCNS.audit(world.path, SM)
        ok = check(tree_digest(world.path) == before,
                   "AC-PCNS5 the probed tree is byte-identical after the audit")
        ok = check(digest(MODULE) == module_before
                   and digest(os.path.join(
                       BASE, "probe_seam_subscript_container_scope.py"))
                   == base_before
                   and digest(RENDER_MODULE) == render_before,
                   "AC-PCNS5 the reading moved no shipped digest") and ok
        ok = check(report["verdict"] == PCNS.SEAMS_COVERED
                   and report["counts"][PCNS.COVERED] >= 1,
                   "AC-PCNS5 the audit still answers a verdict (%r)"
                   % (report["counts"],)) and ok
        refusal = PCNS.reading(os.path.join(world.path, "absent"), SM)
        ok = check(refusal.get("refusal") == PCNS.E_NO_ROOT
                   and refusal.get("probes") == [],
                   "AC-PCNS5 a missing root is refused, not raised (%r)"
                   % (refusal.get("refusal"),)) and ok
    finally:
        world.close()
    return ok


def ac_pcns6():
    """Pure ASCII, stdlib only, no clock, no network, wired once."""
    text = read_text(MODULE)
    suite = read_text(os.path.abspath(__file__))
    ok = check(all(ord(char) < 128 for char in text),
               "AC-PCNS6 the module source is pure ASCII")
    ok = check(all(ord(char) < 128 for char in suite),
               "AC-PCNS6 this suite source is pure ASCII") and ok
    imports = sorted(set(re.findall(r"(?m)^import ([A-Za-z_][A-Za-z0-9_]*)",
                                    text)))
    allowed = ("argparse", "ast", "hashlib", "json", "os", "re", "sys")
    ok = check(not [name for name in imports if name not in allowed],
               "AC-PCNS6 only the allowed stdlib modules are imported (%s)"
               % (",".join(imports),)) and ok
    forbidden = ("time.time", "datetime", "socket", "urllib", "requests",
                 "http.client", "subprocess")
    ok = check(not [token for token in forbidden if token in text],
               "AC-PCNS6 no clock and no network token in the module") and ok
    registry = read_text(REGISTRY)
    ok = check(WIRED_LABEL in registry and WIRED_SUITE in registry,
               "AC-PCNS6 the face and its suite are wired into the registry "
               "exactly once") and ok
    ok = check(registry.count(WIRED_LABEL) == 1
               and registry.count(WIRED_SUITE) == 1,
               "AC-PCNS6 no duplicate registry row") and ok
    ok = check(PCNS.LABEL == "os-probe-seam-nested-subscript-scope",
               "AC-PCNS6 the reconcile label is the face own (%s)"
               % PCNS.LABEL) and ok
    ok = check(PCNS.SEAMS_COVERED == "SEAMS-NESTED-SUBSCRIPT-COVERED",
               "AC-PCNS6 the reading has its own verdict word (%s)"
               % PCNS.SEAMS_COVERED) and ok
    ok = check(PCSC.LABEL == "os-probe-seam-subscript-container-scope"
               and PCFN.LABEL == "os-probe-seam-for-container-name",
               "AC-PCNS6 the shipped faces it extends are still named") and ok
    return ok


def main():
    print("PROBE SEAM NESTED SUBSCRIPT SUITE (AC-PCNS1..AC-PCNS6)")
    results = [ac_pcns1(), ac_pcns2(), ac_pcns3(), ac_pcns4(), ac_pcns5(),
               ac_pcns6()]
    passed = len([item for item in results if item])
    print("SUITE %s %d/%d criteria green"
          % ("PASS" if passed == EXPECTED_CRITERIA else "FAIL",
             passed, EXPECTED_CRITERIA))
    return 0 if passed == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())