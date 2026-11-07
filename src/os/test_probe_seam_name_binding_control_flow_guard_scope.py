"""AC-PNCG1..AC-PNCG6 suite for the guard-aggregating control-flow face (R2545).

Criteria were pinned in state/queue/tech.md:581 at R2543 BEFORE this code
existed.

What this proves: MEASURED at R2543 on the shipped control-flow face own
reader, two arms of one if binding the SAME literal refused although both
agree, two separate if statements bound one name to two values and read as one
guard word, and a nested binding published only the innermost guard. This face
answers all three on top of the shipped law, and every case is checked on BOTH
readers.

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

import probe_seam_name_binding_control_flow_guard_scope as PNCG  # noqa: E402
import probe_seam_name_binding_control_flow_scope as PNCF  # noqa: E402
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(
    BASE, "probe_seam_name_binding_control_flow_guard_scope.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
BASE_MODULE = os.path.join(
    BASE, "probe_seam_name_binding_control_flow_scope.py")
RENDER_MODULE = os.path.join(SANDBOX, "suite_matrix.py")
WIRED_LABEL = '"os-probe-seam-name-binding-control-flow-guard-scope",'
WIRED_SUITE = '"test_probe_seam_name_binding_control_flow_guard_scope.py"), 6),'

HELPER = "pncg_helper"

CONTAINER = 'D = {"a": {"b": ("%s",), "z": ("%s",)}}\n' % (HELPER, HELPER)

SAME_ARMS = (CONTAINER
             + 'if cond:\n'
               '    KEY = "b"\n'
               'else:\n'
               '    KEY = "b"\n'
               'for name in D["a"][KEY]:\n'
               '    pass\n')

DIFF_ARMS = (CONTAINER
             + 'if cond:\n'
               '    KEY = "b"\n'
               'else:\n'
               '    KEY = "z"\n'
               'for name in D["a"][KEY]:\n'
               '    pass\n')

TWO_GROUPS = (CONTAINER
              + 'if cond:\n'
                '    KEY = "b"\n'
                'if other:\n'
                '    KEY = "z"\n'
                'for name in D["a"][KEY]:\n'
                '    pass\n')

NESTED = (CONTAINER
          + 'if outer:\n'
            '    if inner:\n'
            '        KEY = "b"\n'
            'for name in D["a"][KEY]:\n'
            '    pass\n')

UNCONDITIONAL = (CONTAINER
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
    return PNCG.guard_report(text)["loops"]


def base_rows(text):
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
        self.path = tempfile.mkdtemp(prefix="pncg-suite-")
        seams = PNCG.seam_names(SM)
        write_ascii(os.path.join(self.path, HELPER + ".py"),
                    helper_text(seams))

    def write(self, name, text):
        write_ascii(os.path.join(self.path, name), text)
        return name

    def close(self):
        shutil.rmtree(self.path, ignore_errors=True)


def ac_pncg1():
    """Agreeing arms resolve; disagreeing arms still publish both."""
    rows = loop_rows(SAME_ARMS)
    ok = check(len(rows) == 1
               and rows[0]["followed"].get("KEY") == "b"
               and rows[0]["resolved_by_guard"] == ["KEY"],
               "AC-PNCG1 two arms binding the SAME literal resolve (%r)"
               % (rows,))
    ok = check(rows and rows[0]["base_followed"] == {}
               and rows[0]["base_refused"].get("KEY") == "guarded:if:2",
               "AC-PNCG1 the shipped face refused the same fixture (%r)"
               % (rows[0]["base_refused"] if rows else None,)) and ok
    got = PNCG.guard_entry("KEY", SAME_ARMS, "module", 7)
    ok = check(got["state"] == "ok" and got["value"] == "b"
               and got["source"] == PNCG.SOURCE_GUARD,
               "AC-PNCG1 the entry law resolves the agreeing pair (%r)"
               % (got,)) and ok
    diff = loop_rows(DIFF_ARMS)
    ok = check(len(diff) == 1 and diff[0]["arms"]
               and diff[0]["arms"][0]["name"] == "KEY"
               and len(diff[0]["arms"][0]["arms"]) == 2,
               "AC-PNCG1 two arms with different values still publish both "
               "(%r)" % (diff,)) and ok
    ok = check(diff and diff[0]["followed"] == {},
               "AC-PNCG1 the differing pair is still not resolved (%r)"
               % (diff[0]["followed"] if diff else None,)) and ok
    return ok


def ac_pncg2():
    """Two separate if statements publish BOTH groups, not one word."""
    rows = loop_rows(TWO_GROUPS)
    ok = check(len(rows) == 1
               and rows[0]["refused"].get("KEY") == PNCG.REFUSED_GROUPED,
               "AC-PNCG2 two guard groups are named as two groups (%r)"
               % (rows,))
    ok = check(rows and [group["group"] for group in rows[0]["groups"]]
               == ["if:2", "if:4"],
               "AC-PNCG2 both groups are published with their guards (%r)"
               % (rows[0]["groups"] if rows else None,)) and ok
    ok = check(rows and sorted(rows[0]["chains"].get("KEY") or [])
               == ["if:2", "if:4"],
               "AC-PNCG2 both chains are published (%r)"
               % (rows[0]["chains"] if rows else None,)) and ok
    base = base_rows(TWO_GROUPS)
    ok = check(base and base[0]["refused"].get("KEY") == "guarded:if:2",
               "AC-PNCG2 the shipped face published only the first group "
               "(%r)" % (base[0]["refused"] if base else None,)) and ok
    got = PNCG.guard_entry("KEY", TWO_GROUPS, "module", 9)
    ok = check(got["state"] == "refused"
               and got["reason"] == PNCG.REFUSED_GROUPED
               and len(got["groups"]) == 2,
               "AC-PNCG2 the entry law publishes both groups (%r)"
               % (got,)) and ok
    ok = check(rows and rows[0]["followed"] == {},
               "AC-PNCG2 neither group is resolved (%r)"
               % (rows[0]["followed"] if rows else None,)) and ok
    return ok


def ac_pncg3():
    """A nested binding publishes every guard, outermost first."""
    rows = loop_rows(NESTED)
    ok = check(len(rows) == 1
               and rows[0]["refused"].get("KEY")
               == "guarded:if:2>if:3",
               "AC-PNCG3 the nested binding publishes its whole chain (%r)"
               % (rows,))
    ok = check(rows and rows[0]["chains"].get("KEY") == ["if:2>if:3"],
               "AC-PNCG3 the chain is published outermost first (%r)"
               % (rows[0]["chains"] if rows else None,)) and ok
    base = base_rows(NESTED)
    ok = check(base and base[0]["refused"].get("KEY") == "guarded:if:3",
               "AC-PNCG3 the shipped face published only the INNERMOST guard "
               "and dropped the outer one (%r)"
               % (base[0]["refused"] if base else None,)) and ok
    got = PNCG.guard_entry("KEY", NESTED, "module", 8)
    ok = check(got["state"] == "refused"
               and got["reason"] == "guarded:if:2>if:3"
               and got["chains"] == ["if:2>if:3"],
               "AC-PNCG3 the entry law names both guards in order (%r)"
               % (got,)) and ok
    ok = check(rows and rows[0]["followed"] == {},
               "AC-PNCG3 a nested binding is never resolved (%r)"
               % (rows[0]["followed"] if rows else None,)) and ok
    return ok


def ac_pncg4():
    """An unconditional binding wins; shipped answers are carried unchanged."""
    rows = loop_rows(UNCONDITIONAL)
    ok = check(len(rows) == 1 and rows[0]["followed"].get("KEY") == "b"
               and rows[0]["resolved_by_guard"] == [],
               "AC-PNCG4 an unconditional binding still wins (%r)" % (rows,))
    ok = check(rows and rows[0]["base_followed"].get("KEY") == "b",
               "AC-PNCG4 the shipped face agreed (%r)"
               % (rows[0]["base_followed"] if rows else None,)) and ok
    with_rows = loop_rows(WITH_FIXTURE)
    ok = check(len(with_rows) == 1
               and with_rows[0]["refused"].get("KEY") == "with-as",
               "AC-PNCG4 a with-as binding keeps the shipped refusal (%r)"
               % (with_rows,)) and ok
    ok = check(with_rows
               and with_rows[0]["base_refused"].get("KEY") == "with-as",
               "AC-PNCG4 the shipped face named the same shape (%r)"
               % (with_rows[0]["base_refused"] if with_rows else None,)) and ok
    for text, label in ((SAME_ARMS, "agreeing"), (DIFF_ARMS, "differing"),
                        (TWO_GROUPS, "two-group"), (NESTED, "nested"),
                        (UNCONDITIONAL, "unconditional")):
        base = base_rows(text)[0]
        mine = loop_rows(text)[0]
        ok = check(mine["base_followed"] == base["followed"]
                   and mine["base_refused"] == base["refused"],
                   "AC-PNCG4 the shipped answer is carried unchanged on the "
                   "%s fixture (%r vs %r)"
                   % (label, mine["base_followed"], base["followed"])) and ok
    return ok


def ac_pncg5():
    """The reading is read-only: no digest moves across a full audit."""
    world = World()
    try:
        world.write("pncg_probe.py", PROBE_FIXTURE)
        before = tree_digest(world.path)
        module_before = digest(MODULE)
        base_before = digest(BASE_MODULE)
        render_before = digest(RENDER_MODULE)
        report = PNCG.audit(world.path, SM)
        ok = check(tree_digest(world.path) == before,
                   "AC-PNCG5 the probed tree is byte-identical after the "
                   "audit")
        ok = check(digest(MODULE) == module_before
                   and digest(BASE_MODULE) == base_before
                   and digest(RENDER_MODULE) == render_before,
                   "AC-PNCG5 the reading moved no shipped digest") and ok
        row = row_of(report, "pncg_probe.py")
        ok = check(row.get("verdict") == PNCG.COVERED,
                   "AC-PNCG5 the probe row still reads COVERED (%r)"
                   % (row.get("verdict"),)) and ok
        ok = check(row.get("guard_loops")
                   and row["guard_loops"][0]["followed"].get("KEY") == "b",
                   "AC-PNCG5 the row carries this face own guard loop (%r)"
                   % (row.get("guard_loops"),)) and ok
        ok = check(report["tool"] == PNCG.LABEL
                   and report["verdict"] == PNCG.SEAMS_GUARD_COVERED
                   and report["base_tool"] == PNCF.LABEL,
                   "AC-PNCG5 the report keeps the shipped base label and "
                   "answers its own (%r)"
                   % ((report["tool"], report["verdict"],
                       report.get("base_tool")),)) and ok
        refusal = PNCG.reading(os.path.join(world.path, "absent"), SM)
        ok = check(refusal.get("refusal") == PNCG.E_NO_ROOT
                   and refusal.get("probes") == [],
                   "AC-PNCG5 a missing root is refused, not raised (%r)"
                   % (refusal.get("refusal"),)) and ok
    finally:
        world.close()
    return ok


def ac_pncg6():
    """Pure ASCII, stdlib only, no clock, no network, wired once."""
    text = read_text(MODULE)
    suite = read_text(os.path.abspath(__file__))
    ok = check(all(ord(char) < 128 for char in text),
               "AC-PNCG6 the module source is pure ASCII")
    ok = check(all(ord(char) < 128 for char in suite),
               "AC-PNCG6 this suite source is pure ASCII") and ok
    imports = sorted(set(re.findall(r"(?m)^import ([A-Za-z_][A-Za-z0-9_]*)",
                                    text)))
    allowed = ("argparse", "ast", "hashlib", "json", "os", "sys")
    ok = check(not [name for name in imports if name not in allowed],
               "AC-PNCG6 only the allowed stdlib modules are imported (%s)"
               % (",".join(imports),)) and ok
    forbidden = ("time.time", "datetime", "socket", "urllib", "requests",
                 "http.client", "subprocess")
    ok = check(not [token for token in forbidden if token in text],
               "AC-PNCG6 no clock and no network token in the module") and ok
    registry = read_text(REGISTRY)
    ok = check(WIRED_LABEL in registry and WIRED_SUITE in registry,
               "AC-PNCG6 the face and its suite are wired into the registry "
               "exactly once") and ok
    ok = check(registry.count(WIRED_LABEL) == 1
               and registry.count(WIRED_SUITE) == 1,
               "AC-PNCG6 no duplicate registry row") and ok
    ok = check(PNCG.LABEL
               == "os-probe-seam-name-binding-control-flow-guard-scope",
               "AC-PNCG6 the reconcile label is the face own (%s)"
               % PNCG.LABEL) and ok
    ok = check(PNCG.SEAMS_GUARD_COVERED == "SEAMS-GUARD-COVERED"
               and PNCG.SEAMS_GUARD_STALE == "SEAMS-GUARD-STALE",
               "AC-PNCG6 the reading has its own verdict words (%s/%s)"
               % (PNCG.SEAMS_GUARD_COVERED, PNCG.SEAMS_GUARD_STALE)) and ok
    ok = check(PNCG.REFUSED_GROUPED == "guarded-groups"
               and PNCG.CHAIN_SEP == ">"
               and PNCG.REFUSED_GUARDED == "guarded:%s",
               "AC-PNCG6 the new refusal words are its own (%s/%s)"
               % (PNCG.REFUSED_GROUPED, PNCG.CHAIN_SEP)) and ok
    ok = check(PNCF.LABEL
               == "os-probe-seam-name-binding-control-flow-scope",
               "AC-PNCG6 the shipped face it extends is still named") and ok
    return ok


def main():
    print("PROBE SEAM NAME BINDING CONTROL FLOW GUARD SUITE "
          "(AC-PNCG1..AC-PNCG6)")
    results = [ac_pncg1(), ac_pncg2(), ac_pncg3(), ac_pncg4(), ac_pncg5(),
               ac_pncg6()]
    passed = len([item for item in results if item])
    print("SUITE %s %d/%d criteria green"
          % ("PASS" if passed == EXPECTED_CRITERIA else "FAIL",
             passed, EXPECTED_CRITERIA))
    return 0 if passed == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())