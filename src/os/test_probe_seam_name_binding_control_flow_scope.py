"""AC-PNCF1..AC-PNCF6 suite for the seam name-binding control-flow face (R2543).

Criteria were pinned in state/queue/tech.md:579 at R2541 BEFORE this code
existed.

What this proves: MEASURED at R2541 on the shipped position face own reader, a
binding written inside `if False:` still resolves, a `with ... as KEY` binding
is not collected at all so the name reads unbound, and a try/except binding one
name in two exclusive branches reads a single ambiguity word. This face answers
all three on top of the shipped law, and every case is checked on BOTH readers.

Every fixture lives in a string or in a private temporary directory; no shipped
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

import probe_seam_name_binding_control_flow_scope as PNCF  # noqa: E402
import probe_seam_name_binding_position_scope as PNSP  # noqa: E402
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "probe_seam_name_binding_control_flow_scope.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
BASE_MODULE = os.path.join(BASE, "probe_seam_name_binding_position_scope.py")
RENDER_MODULE = os.path.join(SANDBOX, "suite_matrix.py")
WIRED_LABEL = '"os-probe-seam-name-binding-control-flow-scope",'
WIRED_SUITE = '"test_probe_seam_name_binding_control_flow_scope.py"), 6),'

HELPER = "pncf_helper"

CONTAINER = 'D = {"a": {"b": ("%s",), "z": ("%s",)}}\n' % (HELPER, HELPER)

GUARDED_FIXTURE = (CONTAINER
                   + 'if cond:\n'
                     '    KEY = "b"\n'
                     'for name in D["a"][KEY]:\n'
                     '    pass\n')

UNCONDITIONAL_FIXTURE = (CONTAINER
                         + 'KEY = "b"\n'
                           'if cond:\n'
                           '    KEY = "z"\n'
                           'for name in D["a"][KEY]:\n'
                           '    pass\n')

WITH_FIXTURE = (CONTAINER
                + 'with open("x") as KEY:\n'
                  '    pass\n'
                  'for name in D["a"][KEY]:\n'
                  '    pass\n')

ARMS_FIXTURE = (CONTAINER
                + 'if cond:\n'
                  '    KEY = "b"\n'
                  'else:\n'
                  '    KEY = "z"\n'
                  'for name in D["a"][KEY]:\n'
                  '    pass\n')

LOOP_FIXTURE = (CONTAINER
                + 'for i in range(3):\n'
                  '    KEY = "b"\n'
                  'for name in D["a"][KEY]:\n'
                  '    pass\n')

PROBE_FIXTURE = ('import importlib\n'
                 '\n'
                 + CONTAINER
                 + 'KEY = "b"\n'
                   'for name in D["a"][KEY]:\n'
                   '    importlib.import_module(name).QUIETED\n')


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
    return PNCF.control_flow_report(text)["loops"]


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
        self.path = tempfile.mkdtemp(prefix="pncf-suite-")
        seams = PNCF.seam_names(SM)
        write_ascii(os.path.join(self.path, HELPER + ".py"),
                    helper_text(seams))

    def write(self, name, text):
        write_ascii(os.path.join(self.path, name), text)
        return name

    def close(self):
        shutil.rmtree(self.path, ignore_errors=True)


def ac_pncf1():
    """A guarded binding is NAMED with its guard and never resolved."""
    rows = loop_rows(GUARDED_FIXTURE)
    ok = check(len(rows) == 1
               and rows[0]["followed"] == {}
               and rows[0]["refused"].get("KEY") == "guarded:if:2",
               "AC-PNCF1 a binding inside a branch is NAMED with its guard "
               "and never resolved (%r)" % (rows,))
    ok = check(rows and rows[0]["base_followed"].get("KEY") == "b",
               "AC-PNCF1 the shipped position face resolved the same binding "
               "(%r)" % (rows,)) and ok
    got = PNCF.control_flow_entry("KEY", GUARDED_FIXTURE, "module", 4)
    ok = check(got["state"] == "refused"
               and got["reason"] == "guarded:if:2",
               "AC-PNCF1 the entry law refuses the guarded shape (%r)"
               % (got,)) and ok
    rows = loop_rows(UNCONDITIONAL_FIXTURE)
    ok = check(rows and rows[0]["followed"].get("KEY") == "b"
               and rows[0]["refused"] == {},
               "AC-PNCF1 an unconditional binding still resolves even when a "
               "later branch rebinds the name (%r)" % (rows,)) and ok
    return ok


def ac_pncf2():
    """A with-as binding is NAMED with that shape, never silently unbound."""
    rows = loop_rows(WITH_FIXTURE)
    ok = check(len(rows) == 1
               and rows[0]["refused"].get("KEY") == PNCF.REFUSED_WITH_AS,
               "AC-PNCF2 a with-as binding is NAMED with its shape (%r)"
               % (rows,))
    ok = check(rows and rows[0]["base_refused"].get("KEY") == "unbound",
               "AC-PNCF2 the shipped position face read that same name "
               "unbound (%r)" % (rows,)) and ok
    got = PNCF.control_flow_entry("KEY", WITH_FIXTURE, "module", 4)
    ok = check(got["state"] == "refused" and got["reason"] == "with-as",
               "AC-PNCF2 the entry law answers the with-as shape (%r)"
               % (got,)) and ok
    ok = check(PNCF.REFUSED_WITH_AS == "with-as"
               and PNCF.REFUSED_WITH_AS != "unbound",
               "AC-PNCF2 the new word is its own (%s)"
               % PNCF.REFUSED_WITH_AS) and ok
    return ok


def ac_pncf3():
    """Two exclusive arms of one branch publish BOTH arms by name."""
    rows = loop_rows(ARMS_FIXTURE)
    arms = rows[0]["arms"] if rows else []
    ok = check(len(rows) == 1 and len(arms) == 1
               and arms[0]["name"] == "KEY",
               "AC-PNCF3 one row publishes the arms pair (%r)" % (rows,))
    published = {item["arm"]: item["value"] for item in arms[0]["arms"]} \
        if arms else {}
    ok = check(published == {"body": "b", "else": "z"},
               "AC-PNCF3 both arms are published with their values (%r)"
               % (published,)) and ok
    ok = check(rows and rows[0]["refused"] == {},
               "AC-PNCF3 no ambiguity word is produced for exclusive arms (%r)"
               % (rows,)) and ok
    got = PNCF.control_flow_entry("KEY", ARMS_FIXTURE, "module", 6)
    ok = check(got["state"] == PNCF.STATE_ARMS
               and got["reason"] == "exclusive-arms"
               and [item["arm"] for item in got["arms"]] == ["body", "else"],
               "AC-PNCF3 the entry law answers both arms (%r)" % (got,)) and ok
    base = PNSP.position_entry("KEY", ARMS_FIXTURE, "module", 6)
    ok = check(base["state"] == "refused" and base["reason"] == "ambiguous",
               "AC-PNCF3 the shipped face read one ambiguity word (%r)"
               % (base,)) and ok
    return ok


def ac_pncf4():
    """A binding inside a loop body that may run zero times is NAMED."""
    rows = loop_rows(LOOP_FIXTURE)
    targets = [row for row in rows if row["refused"].get("KEY")]
    ok = check(len(rows) == 2 and len(targets) == 1
               and targets[0]["refused"]["KEY"] == "guarded:loop:2",
               "AC-PNCF4 a binding inside a loop body is NAMED with its "
               "guard (%r)" % (rows,))
    ok = check(targets and targets[0]["base_followed"].get("KEY") == "b",
               "AC-PNCF4 the shipped face resolved the same guarded binding "
               "(%r)" % (targets,)) and ok
    got = PNCF.control_flow_entry("KEY", LOOP_FIXTURE, "module", 4)
    ok = check(got["state"] == "refused"
               and got["reason"] == "guarded:loop:2",
               "AC-PNCF4 the entry law refuses the loop-guarded shape (%r)"
               % (got,)) and ok
    handler = ('D = {"a": {"b": ("%s",)}}\n'
               'try:\n'
               '    KEY = "b"\n'
               'except ValueError:\n'
               '    pass\n'
               'for name in D["a"][KEY]:\n'
               '    pass\n' % HELPER)
    got = PNCF.control_flow_entry("KEY", handler, "module", 6)
    ok = check(got["state"] == "refused"
               and got["reason"].startswith("guarded:try:"),
               "AC-PNCF4 a binding inside a try arm is NAMED with its guard "
               "(%r)" % (got,)) and ok
    return ok


def ac_pncf5():
    """The reading is read-only: no digest moves across a full audit."""
    world = World()
    try:
        world.write("pncf_probe.py", PROBE_FIXTURE)
        before = tree_digest(world.path)
        module_before = digest(MODULE)
        base_before = digest(BASE_MODULE)
        render_before = digest(RENDER_MODULE)
        report = PNCF.audit(world.path, SM)
        ok = check(tree_digest(world.path) == before,
                   "AC-PNCF5 the probed tree is byte-identical after the "
                   "audit")
        ok = check(digest(MODULE) == module_before
                   and digest(BASE_MODULE) == base_before
                   and digest(RENDER_MODULE) == render_before,
                   "AC-PNCF5 the reading moved no shipped digest") and ok
        row = row_of(report, "pncf_probe.py")
        ok = check(row.get("verdict") == PNCF.COVERED,
                   "AC-PNCF5 the probe row still reads COVERED (%r)"
                   % (row.get("verdict"),)) and ok
        ok = check(row.get("control_flow_loops")
                   and row["control_flow_loops"][0]["followed"].get("KEY")
                   == "b",
                   "AC-PNCF5 the row carries this face own flow loop (%r)"
                   % (row.get("control_flow_loops"),)) and ok
        ok = check(report["tool"] == PNCF.LABEL
                   and report["verdict"] == PNCF.SEAMS_COVERED
                   and report["base_tool"] == PNSP.LABEL,
                   "AC-PNCF5 the report keeps the shipped base label and "
                   "answers its own (%r)"
                   % ((report["tool"], report["verdict"],
                       report.get("base_tool")),)) and ok
        refusal = PNCF.reading(os.path.join(world.path, "absent"), SM)
        ok = check(refusal.get("refusal") == PNCF.E_NO_ROOT
                   and refusal.get("probes") == [],
                   "AC-PNCF5 a missing root is refused, not raised (%r)"
                   % (refusal.get("refusal"),)) and ok
    finally:
        world.close()
    return ok


def ac_pncf6():
    """Pure ASCII, stdlib only, no clock, no network, wired once."""
    text = read_text(MODULE)
    suite = read_text(os.path.abspath(__file__))
    ok = check(all(ord(char) < 128 for char in text),
               "AC-PNCF6 the module source is pure ASCII")
    ok = check(all(ord(char) < 128 for char in suite),
               "AC-PNCF6 this suite source is pure ASCII") and ok
    imports = sorted(set(re.findall(r"(?m)^import ([A-Za-z_][A-Za-z0-9_]*)",
                                    text)))
    allowed = ("argparse", "ast", "hashlib", "json", "os", "sys")
    ok = check(not [name for name in imports if name not in allowed],
               "AC-PNCF6 only the allowed stdlib modules are imported (%s)"
               % (",".join(imports),)) and ok
    forbidden = ("time.time", "datetime", "socket", "urllib", "requests",
                 "http.client", "subprocess")
    ok = check(not [token for token in forbidden if token in text],
               "AC-PNCF6 no clock and no network token in the module") and ok
    registry = read_text(REGISTRY)
    ok = check(WIRED_LABEL in registry and WIRED_SUITE in registry,
               "AC-PNCF6 the face and its suite are wired into the registry "
               "exactly once") and ok
    ok = check(registry.count(WIRED_LABEL) == 1
               and registry.count(WIRED_SUITE) == 1,
               "AC-PNCF6 no duplicate registry row") and ok
    ok = check(PNCF.LABEL == "os-probe-seam-name-binding-control-flow-scope",
               "AC-PNCF6 the reconcile label is the face own (%s)"
               % PNCF.LABEL) and ok
    ok = check(PNCF.SEAMS_COVERED == "SEAMS-CONTROL-FLOW-COVERED"
               and PNCF.SEAMS_STALE == "SEAMS-CONTROL-FLOW-STALE",
               "AC-PNCF6 the reading has its own verdict words (%s/%s)"
               % (PNCF.SEAMS_COVERED, PNCF.SEAMS_STALE)) and ok
    ok = check(PNCF.REFUSED_GUARDED == "guarded:%s"
               and PNCF.STATE_ARMS == "arms",
               "AC-PNCF6 the new refusal words are its own (%s/%s)"
               % (PNCF.REFUSED_GUARDED, PNCF.STATE_ARMS)) and ok
    ok = check(PNSP.LABEL == "os-probe-seam-name-binding-position-scope",
               "AC-PNCF6 the shipped face it extends is still named") and ok
    return ok


def main():
    print("PROBE SEAM NAME BINDING CONTROL FLOW SUITE (AC-PNCF1..AC-PNCF6)")
    results = [ac_pncf1(), ac_pncf2(), ac_pncf3(), ac_pncf4(), ac_pncf5(),
               ac_pncf6()]
    passed = len([item for item in results if item])
    print("SUITE %s %d/%d criteria green"
          % ("PASS" if passed == EXPECTED_CRITERIA else "FAIL",
             passed, EXPECTED_CRITERIA))
    return 0 if passed == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())