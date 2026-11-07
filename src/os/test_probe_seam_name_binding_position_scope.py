"""AC-PNSP1..AC-PNSP6 suite for the seam name-binding position face (R2541).

Criteria were pinned in state/queue/tech.md:577 at R2539 BEFORE this code
existed.

What this proves: MEASURED at R2539 on the shipped scope face own reader, the
bindings are read per SCOPE and not per POSITION (so a loop that runs before
its key is bound reads like one that runs after), a class body is not a scope
that reading follows, and a comprehension loop is dropped silently. This face
answers all three on top of the shipped law.

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

import probe_seam_name_binding_position_scope as PNSP  # noqa: E402
import probe_seam_name_binding_scope_awareness as PNSB  # noqa: E402
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "probe_seam_name_binding_position_scope.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
BASE_MODULE = os.path.join(BASE, "probe_seam_name_binding_scope_awareness.py")
RENDER_MODULE = os.path.join(SANDBOX, "suite_matrix.py")
WIRED_LABEL = '"os-probe-seam-name-binding-position-scope",'
WIRED_SUITE = '"test_probe_seam_name_binding_position_scope.py"), 6),'

HELPER = "pnsp_helper"

AFTER_FIXTURE = ('D = {"a": {"b": ("%s",)}}\n'
                 '\n'
                 'for name in D["a"][KEY]:\n'
                 '    pass\n'
                 '\n'
                 'KEY = "b"\n' % HELPER)

BEFORE_FIXTURE = ('D = {"a": {"b": ("%s",)}}\n'
                  'KEY = "b"\n'
                  '\n'
                  'for name in D["a"][KEY]:\n'
                  '    pass\n' % HELPER)

CLASS_FIXTURE = ('D = {"a": {"b": ("%s",), "c": ("%s",)}}\n'
                 'KEY = "b"\n'
                 '\n'
                 'class Room:\n'
                 '    KEY = "c"\n'
                 '    for name in D["a"][KEY]:\n'
                 '        pass\n' % (HELPER, HELPER))

CLASS_ONLY_FIXTURE = ('D = {"a": {"b": ("%s",)}}\n'
                      '\n'
                      'class Room:\n'
                      '    KEY = "b"\n'
                      '    for name in D["a"][KEY]:\n'
                      '        pass\n' % HELPER)

REBOUND_FIXTURE = ('D = {"a": {"b": ("%s",), "z": ("%s",)}}\n'
                   'KEY = "b"\n'
                   '\n'
                   'for name in D["a"][KEY]:\n'
                   '    pass\n'
                   '\n'
                   'KEY = "z"\n' % (HELPER, HELPER))

COMPREHENSION_FIXTURE = ('D = {"a": {"b": ("%s",)}}\n'
                         'KEY = "b"\n'
                         '\n'
                         'vals = [item for item in D["a"][KEY]]\n'
                         'gen = tuple(other for other in D["a"][KEY])\n'
                         % HELPER)

PROBE_FIXTURE = ('import importlib\n'
                 '\n'
                 'D = {"a": {"b": ("%s",)}}\n'
                 'KEY = "b"\n'
                 '\n'
                 'for name in D["a"][KEY]:\n'
                 '    importlib.import_module(name).QUIETED\n' % HELPER)


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
    return PNSP.position_report(text)["loops"]


def for_rows(text):
    return [row for row in loop_rows(text) if row["kind"] == "for"]


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
        self.path = tempfile.mkdtemp(prefix="pnsp-suite-")
        seams = PNSP.seam_names(SM)
        write_ascii(os.path.join(self.path, HELPER + ".py"),
                    helper_text(seams))

    def write(self, name, text):
        write_ascii(os.path.join(self.path, name), text)
        return name

    def close(self):
        shutil.rmtree(self.path, ignore_errors=True)


def ac_pnsp1():
    """A binding that PRECEDES the loop resolves; one that follows does not."""
    rows = for_rows(BEFORE_FIXTURE)
    ok = check(len(rows) == 1
               and rows[0]["followed"].get("KEY") == "b"
               and rows[0]["refused"] == {},
               "AC-PNSP1 a binding written before the loop resolves (%r)"
               % (rows,))
    rows = for_rows(AFTER_FIXTURE)
    ok = check(len(rows) == 1
               and rows[0]["followed"] == {}
               and rows[0]["refused"].get("KEY")
               == PNSP.REFUSED_NOT_YET_BOUND,
               "AC-PNSP1 a binding written after the loop is NAMED "
               "not-yet-bound and never resolved (%r)" % (rows,)) and ok
    ok = check(rows and rows[0]["later"].get("KEY") == "b",
               "AC-PNSP1 and the later write is published as a fact (%r)"
               % (rows,)) and ok
    got = PNSP.position_entry("KEY", AFTER_FIXTURE, "module", 3)
    ok = check(got["state"] == "refused"
               and got["reason"] == PNSP.REFUSED_NOT_YET_BOUND,
               "AC-PNSP1 the entry law refuses the same shape (%r)"
               % (got,)) and ok
    got = PNSP.position_entry("KEY", BEFORE_FIXTURE, "module", 4)
    ok = check(got["state"] == "ok" and got["value"] == "b",
               "AC-PNSP1 the same name resolves at a later loop line (%r)"
               % (got,)) and ok
    return ok


def ac_pnsp2():
    """A class body is its own scope and a module name is announced shadowed."""
    rows = for_rows(CLASS_FIXTURE)
    ok = check(len(rows) == 1 and rows[0]["scope"] == "class:Room",
               "AC-PNSP2 the loop is attributed to the class body (%r)"
               % (rows,))
    ok = check(rows and rows[0]["followed"].get("KEY") == "c"
               and rows[0]["taken_from"].get("KEY") == "class:Room",
               "AC-PNSP2 the class constant resolves for a loop in that "
               "class (%r)" % (rows,)) and ok
    ok = check(rows and rows[0]["shadowed"] == ["KEY"],
               "AC-PNSP2 the module name of the same name is announced as "
               "shadowed (%r)" % (rows,)) and ok
    rows = for_rows(CLASS_ONLY_FIXTURE)
    ok = check(rows and rows[0]["followed"].get("KEY") == "b"
               and rows[0]["shadowed"] == [],
               "AC-PNSP2 a class-only constant resolves with no shadow "
               "claimed (%r)" % (rows,)) and ok
    got = PNSP.position_entry("KEY", CLASS_FIXTURE, "class:Room", 6)
    ok = check(got["state"] == "ok" and got["value"] == "c"
               and got["shadow"],
               "AC-PNSP2 the entry law answers the class scope directly (%r)"
               % (got,)) and ok
    got = PNSP.position_entry("KEY", CLASS_FIXTURE, "module", 6)
    ok = check(got["state"] == "ok" and got["value"] == "b"
               and not got["shadow"],
               "AC-PNSP2 a module-level reading still sees the module value "
               "(%r)" % (got,)) and ok
    return ok


def ac_pnsp3():
    """A name rebound AFTER the loop resolves to the earlier value."""
    rows = for_rows(REBOUND_FIXTURE)
    ok = check(len(rows) == 1 and rows[0]["followed"].get("KEY") == "b",
               "AC-PNSP3 the loop resolves the value written before it (%r)"
               % (rows,))
    ok = check(rows and rows[0]["later"].get("KEY") == "z",
               "AC-PNSP3 the later rebinding is published on the row (%r)"
               % (rows,)) and ok
    ok = check(rows and rows[0]["refused"] == {},
               "AC-PNSP3 the rebinding does not make the name ambiguous "
               "(%r)" % (rows,)) and ok
    got = PNSP.position_entry("KEY", REBOUND_FIXTURE, "module", 4)
    ok = check(got["state"] == "ok" and got["value"] == "b"
               and got["later"].get("KEY") == "z",
               "AC-PNSP3 the entry law carries both the value and the "
               "later write (%r)" % (got,)) and ok
    twice = ('D = {"a": {"b": ("%s",)}}\n'
             'KEY = "b"\n'
             'KEY = "zzz"\n'
             'for name in D["a"][KEY]:\n'
             '    pass\n' % HELPER)
    got = PNSP.position_entry("KEY", twice, "module", 4)
    ok = check(got["state"] == "refused" and got["reason"] == "ambiguous",
               "AC-PNSP3 two bindings BEFORE the loop stay ambiguous (%r)"
               % (got,)) and ok
    return ok


def ac_pnsp4():
    """A loop spelled inside a comprehension is NAMED, not dropped."""
    rows = loop_rows(COMPREHENSION_FIXTURE)
    kinds = [row["kind"] for row in rows]
    ok = check("comprehension:list" in kinds,
               "AC-PNSP4 the list comprehension loop is read (%r)" % (rows,))
    ok = check("comprehension:generator" in kinds,
               "AC-PNSP4 the generator comprehension loop is read (%r)"
               % (rows,)) and ok
    ok = check(not [row for row in rows if row["kind"] == "for"],
               "AC-PNSP4 the reading does not invent a plain for-loop (%r)"
               % (rows,)) and ok
    for row in rows:
        if row["kind"].startswith("comprehension:"):
            ok = check(row["followed"].get("KEY") == "b"
                       and row["refused"] == {},
                       "AC-PNSP4 %s resolves the preceding constant (%r)"
                       % (row["kind"], row)) and ok
    got = PNSP.position_report(COMPREHENSION_FIXTURE)
    ok = check([clause for clause in got["loops"]
                if clause["scope"] == "module"],
               "AC-PNSP4 the comprehension rows carry their scope (%r)"
               % (got["loops"],)) and ok
    return ok


def ac_pnsp5():
    """The reading is read-only: no digest moves across a full audit."""
    world = World()
    try:
        world.write("pnsp_probe.py", PROBE_FIXTURE)
        before = tree_digest(world.path)
        module_before = digest(MODULE)
        base_before = digest(BASE_MODULE)
        render_before = digest(RENDER_MODULE)
        report = PNSP.audit(world.path, SM)
        ok = check(tree_digest(world.path) == before,
                   "AC-PNSP5 the probed tree is byte-identical after the "
                   "audit")
        ok = check(digest(MODULE) == module_before
                   and digest(BASE_MODULE) == base_before
                   and digest(RENDER_MODULE) == render_before,
                   "AC-PNSP5 the reading moved no shipped digest") and ok
        row = row_of(report, "pnsp_probe.py")
        ok = check(row.get("verdict") == PNSP.COVERED,
                   "AC-PNSP5 the probe row still reads COVERED (%r)"
                   % (row.get("verdict"),)) and ok
        ok = check(row.get("position_loops")
                   and row["position_loops"][0]["followed"].get("KEY") == "b",
                   "AC-PNSP5 the row carries this face own position loop (%r)"
                   % (row.get("position_loops"),)) and ok
        ok = check(report["tool"] == PNSP.LABEL
                   and report["verdict"] == PNSP.SEAMS_COVERED
                   and report["base_tool"] == PNSB.LABEL,
                   "AC-PNSP5 the report keeps the shipped base label and "
                   "answers its own (%r)"
                   % ((report["tool"], report["verdict"],
                       report.get("base_tool")),)) and ok
        refusal = PNSP.reading(os.path.join(world.path, "absent"), SM)
        ok = check(refusal.get("refusal") == PNSP.E_NO_ROOT
                   and refusal.get("probes") == [],
                   "AC-PNSP5 a missing root is refused, not raised (%r)"
                   % (refusal.get("refusal"),)) and ok
    finally:
        world.close()
    return ok


def ac_pnsp6():
    """Pure ASCII, stdlib only, no clock, no network, wired once."""
    text = read_text(MODULE)
    suite = read_text(os.path.abspath(__file__))
    ok = check(all(ord(char) < 128 for char in text),
               "AC-PNSP6 the module source is pure ASCII")
    ok = check(all(ord(char) < 128 for char in suite),
               "AC-PNSP6 this suite source is pure ASCII") and ok
    imports = sorted(set(re.findall(r"(?m)^import ([A-Za-z_][A-Za-z0-9_]*)",
                                    text)))
    allowed = ("argparse", "ast", "hashlib", "json", "os", "sys")
    ok = check(not [name for name in imports if name not in allowed],
               "AC-PNSP6 only the allowed stdlib modules are imported (%s)"
               % (",".join(imports),)) and ok
    forbidden = ("time.time", "datetime", "socket", "urllib", "requests",
                 "http.client", "subprocess")
    ok = check(not [token for token in forbidden if token in text],
               "AC-PNSP6 no clock and no network token in the module") and ok
    registry = read_text(REGISTRY)
    ok = check(WIRED_LABEL in registry and WIRED_SUITE in registry,
               "AC-PNSP6 the face and its suite are wired into the registry "
               "exactly once") and ok
    ok = check(registry.count(WIRED_LABEL) == 1
               and registry.count(WIRED_SUITE) == 1,
               "AC-PNSP6 no duplicate registry row") and ok
    ok = check(PNSP.LABEL == "os-probe-seam-name-binding-position-scope",
               "AC-PNSP6 the reconcile label is the face own (%s)"
               % PNSP.LABEL) and ok
    ok = check(PNSP.SEAMS_COVERED == "SEAMS-POSITION-COVERED"
               and PNSP.SEAMS_STALE == "SEAMS-POSITION-STALE",
               "AC-PNSP6 the reading has its own verdict words (%s/%s)"
               % (PNSP.SEAMS_COVERED, PNSP.SEAMS_STALE)) and ok
    ok = check(PNSP.REFUSED_NOT_YET_BOUND == "not-yet-bound",
               "AC-PNSP6 the new refusal word is its own (%s)"
               % PNSP.REFUSED_NOT_YET_BOUND) and ok
    ok = check(PNSB.LABEL == "os-probe-seam-name-binding-scope-awareness",
               "AC-PNSP6 the shipped face it extends is still named") and ok
    return ok


def main():
    print("PROBE SEAM NAME BINDING POSITION SUITE (AC-PNSP1..AC-PNSP6)")
    results = [ac_pnsp1(), ac_pnsp2(), ac_pnsp3(), ac_pnsp4(), ac_pnsp5(),
               ac_pnsp6()]
    passed = len([item for item in results if item])
    print("SUITE %s %d/%d criteria green"
          % ("PASS" if passed == EXPECTED_CRITERIA else "FAIL",
             passed, EXPECTED_CRITERIA))
    return 0 if passed == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())