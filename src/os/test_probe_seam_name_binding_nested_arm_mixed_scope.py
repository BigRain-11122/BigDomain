"""AC-PNDP1..AC-PNDP6 suite for the nested arm mixed scope face (R2551).

Criteria were pinned in state/queue/tech.md:587 at R2549 BEFORE this code
existed.

What this proves: MEASURED at R2549 on the shipped nested face own reader, an
arm that binds the name directly AND contains a nested guard reads
`mixed:<arm>` and never resolves even when every leaf agrees, a try with an
else reads `incomplete:<group>`, and a `with ... as KEY` arm reads
`non-literal:<arm>`. This face merges a direct arm binding with an agreeing
nested tree, treats an else that rebinds the same literal as coverage, and
names a with-as arm instead of using a shape word.

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

import probe_seam_name_binding_nested_arm_mixed_scope as PNDP  # noqa: E402
import probe_seam_name_binding_nested_exhaustive_path as PNCD  # noqa: E402
import probe_seam_name_binding_control_flow_guard_exhaustive as PNCT  # noqa: E402
import probe_seam_name_binding_control_flow_guard_scope as PNCG  # noqa: E402
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(
    BASE, "probe_seam_name_binding_nested_arm_mixed_scope.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
NESTED_MODULE = os.path.join(
    BASE, "probe_seam_name_binding_nested_exhaustive_path.py")
EXH_MODULE = os.path.join(
    BASE, "probe_seam_name_binding_control_flow_guard_exhaustive.py")
GUARD_MODULE = os.path.join(
    BASE, "probe_seam_name_binding_control_flow_guard_scope.py")
RENDER_MODULE = os.path.join(SANDBOX, "suite_matrix.py")
WIRED_LABEL = '"os-probe-seam-name-binding-nested-arm-mixed-scope",'
WIRED_SUITE = '"test_probe_seam_name_binding_nested_arm_mixed_scope.py"),'

HELPER = "pndp_helper"

CONTAINER = ('D = {"a": {"b": ("%s",), "z": ("%s",)}}\n'
             % (HELPER, HELPER))

TAIL = 'for name in D["a"][KEY]:\n    pass\n'

MIX_AGREE = (CONTAINER
             + 'if a1:\n'
               '    KEY = "b"\n'
               '    if a2:\n'
               '        KEY = "b"\n'
               '    else:\n'
               '        KEY = "b"\n'
               'else:\n'
               '    KEY = "b"\n'
             + TAIL)

MIX_DEEP = (CONTAINER
            + 'if a1:\n'
              '    KEY = "b"\n'
              '    if a2:\n'
              '        if a3:\n'
              '            KEY = "b"\n'
              '        else:\n'
              '            KEY = "b"\n'
              '    else:\n'
              '        KEY = "b"\n'
              'else:\n'
              '    KEY = "b"\n'
            + TAIL)

MIX_DIFF = (CONTAINER
            + 'if a1:\n'
              '    KEY = "b"\n'
              '    if a2:\n'
              '        KEY = "b"\n'
              '    else:\n'
              '        KEY = "z"\n'
              'else:\n'
              '    KEY = "b"\n'
            + TAIL)

TRY_ELSE_AGREE = (CONTAINER
                  + 'try:\n'
                    '    KEY = "b"\n'
                    'except Exception:\n'
                    '    KEY = "b"\n'
                    'else:\n'
                    '    KEY = "b"\n'
                  + TAIL)

TRY_ELSE_EMPTY = (CONTAINER
                  + 'try:\n'
                    '    KEY = "b"\n'
                    'except Exception:\n'
                    '    KEY = "b"\n'
                    'else:\n'
                    '    pass\n'
                  + TAIL)

TRY_FINALLY = (CONTAINER
               + 'try:\n'
                 '    KEY = "b"\n'
                 'except Exception:\n'
                 '    KEY = "b"\n'
                 'finally:\n'
                 '    pass\n'
               + TAIL)

WITH_AS = (CONTAINER
           + 'if a1:\n'
             '    with open("x") as KEY:\n'
             '        pass\n'
             'else:\n'
             '    KEY = "b"\n'
           + TAIL)

NESTED_ONLY = (CONTAINER
               + 'if a1:\n'
                 '    if a2:\n'
                 '        KEY = "b"\n'
                 '    else:\n'
                 '        KEY = "b"\n'
               'else:\n'
               '    KEY = "b"\n'
               + TAIL)

NO_ELSE = (CONTAINER
           + 'if a1:\n'
             '    KEY = "b"\n'
           + TAIL)

PROBE_FIXTURE = ('import importlib\n'
                 '\n'
                 + CONTAINER
                 + 'if a1:\n'
                   '    KEY = "b"\n'
                   '    if a2:\n'
                   '        KEY = "b"\n'
                   '    else:\n'
                   '        KEY = "b"\n'
                   'else:\n'
                   '    KEY = "b"\n'
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
    return PNDP.arm_report(text)["loops"]


def nested_rows(text):
    return PNCD.nested_report(text)["loops"]


def base_rows(text):
    return PNCT.exhaustive_report(text)["loops"]


def guard_rows(text):
    return PNCG.guard_report(text)["loops"]


def tail_row(text):
    rows = loop_rows(text)
    return rows[-1] if rows else {}


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
        self.path = tempfile.mkdtemp(prefix="pndp-suite-")
        seams = PNDP.seam_names(SM)
        write_ascii(os.path.join(self.path, HELPER + ".py"),
                    helper_text(seams))

    def write(self, name, text):
        write_ascii(os.path.join(self.path, name), text)
        return name

    def close(self):
        shutil.rmtree(self.path, ignore_errors=True)


def ac_pndp1():
    """A direct arm binding plus an agreeing nested tree resolves."""
    row = tail_row(MIX_AGREE)
    ok = check(row and row["followed"].get("KEY") == "b"
               and row["resolved_by_arm_mixed"] == ["KEY"],
               "AC-PNDP1 a direct plus agreeing nested tree resolves (%r)"
               % (row.get("followed") if row else None,))
    ok = check(row and row["base_nested_refused"].get("KEY") == "mixed:body"
               and row["base_nested_followed"] == {},
               "AC-PNDP1 the nested face refused the same tree (%r)"
               % (row.get("base_nested_refused") if row else None,)) and ok
    leaves = row["leaves"].get("KEY") if row else None
    ok = check(leaves and [item["path"] for item in leaves]
               == ["if:2/body", "if:2/body>if:4/body",
                   "if:2/body>if:4/else", "if:2/else"]
               and [item["value"] for item in leaves] == ["b", "b", "b", "b"],
               "AC-PNDP1 every leaf including the direct one is published "
               "(%r)" % (leaves,)) and ok
    got = PNDP.arm_entry("KEY", MIX_AGREE, "module", 10)
    ok = check(got["state"] == "ok" and got["value"] == "b"
               and got["source"] == PNDP.SOURCE_ARM_MIXED
               and got["root"] == "if:2"
               and got["base_nested_reason"] == "mixed:body",
               "AC-PNDP1 the entry law merges to the ROOT group (%r)"
               % (got,)) and ok
    deep = tail_row(MIX_DEEP)
    ok = check(deep and deep["followed"].get("KEY") == "b"
               and deep["resolved_by_arm_mixed"] == ["KEY"],
               "AC-PNDP1 a three-deep agreeing tree also resolves (%r)"
               % (deep.get("followed") if deep else None,)) and ok
    return ok


def ac_pndp2():
    """A direct binding that disagrees publishes both and resolves nothing."""
    row = tail_row(MIX_DIFF)
    ok = check(row and row["followed"] == {} and len(row["arms"]) == 1,
               "AC-PNDP2 a disagreeing tree resolves nothing (%r)"
               % (row.get("followed") if row else None,))
    inner = row["arms"][0]["arms"] if row and row["arms"] else None
    ok = check(isinstance(inner, list) and len(inner) == 2
               and inner[0]["state"] == "arms"
               and inner[0]["reason"] == "disagree:body"
               and inner[0]["values"] == ["b", "z"]
               and inner[1]["state"] == "ok",
               "AC-PNDP2 the fold names the disagreeing arm (%r)"
               % (inner,)) and ok
    leaves = row["leaves"].get("KEY") if row else None
    ok = check(leaves and [item["path"] for item in leaves]
               == ["if:2/body", "if:2/body>if:4/body",
                   "if:2/body>if:4/else", "if:2/else"]
               and [item["value"] for item in leaves] == ["b", "b", "z", "b"],
               "AC-PNDP2 both values are published by full path (%r)"
               % (leaves,)) and ok
    got = PNDP.arm_entry("KEY", MIX_DIFF, "module", 10)
    ok = check(got["state"] == "arms" and got["value"] is None
               and got["values"] == ["b", "z"]
               and got["reason"] == PNDP.REFUSED_NESTED_ARMS,
               "AC-PNDP2 the entry law refuses to pick a leaf (%r)"
               % (got,)) and ok
    return ok


def ac_pndp3():
    """A try with an agreeing else is coverage; an empty else is partial."""
    row = tail_row(TRY_ELSE_AGREE)
    ok = check(row and row["followed"].get("KEY") == "b"
               and row["resolved_by_arm_mixed"] == ["KEY"],
               "AC-PNDP3 a try whose else rebinds the literal resolves (%r)"
               % (row.get("followed") if row else None,))
    ok = check(row and row["base_nested_refused"].get("KEY")
               == "incomplete:try:2",
               "AC-PNDP3 the nested face refused the same try (%r)"
               % (row.get("base_nested_refused") if row else None,)) and ok
    leaves = row["leaves"].get("KEY") if row else None
    ok = check(leaves and [item["path"] for item in leaves]
               == ["try:2/body", "try:2/except0", "try:2/else"],
               "AC-PNDP3 the else arm is counted as coverage (%r)"
               % (leaves,)) and ok
    empty = tail_row(TRY_ELSE_EMPTY)
    ok = check(empty and empty["followed"] == {}
               and empty["refused"].get("KEY") == "partial:else"
               and empty["partial"].get("KEY") == "else",
               "AC-PNDP3 an else binding nothing is named partial:else (%r)"
               % (empty.get("refused") if empty else None,)) and ok
    got = PNDP.arm_entry("KEY", TRY_ELSE_EMPTY, "module", 8)
    ok = check(got["state"] == "refused" and got["reason"] == "partial:else"
               and got["value"] is None,
               "AC-PNDP3 the entry law never resolves an empty else (%r)"
               % (got,)) and ok
    finally_row = tail_row(TRY_FINALLY)
    ok = check(finally_row and finally_row["refused"].get("KEY")
               == "incomplete:try:2",
               "AC-PNDP3 a finally is still refused as incomplete (%r)"
               % (finally_row.get("refused") if finally_row else None,)) and ok
    return ok


def ac_pndp4():
    """A with-as binding inside an arm is NAMED and never resolved."""
    row = tail_row(WITH_AS)
    ok = check(row and row["refused"].get("KEY") == "with-as:body"
               and row["followed"] == {},
               "AC-PNDP4 the with-as arm is named with-as:body (%r)"
               % (row.get("refused") if row else None,))
    ok = check(row and row["base_nested_refused"].get("KEY")
               == "non-literal:body",
               "AC-PNDP4 the nested face used a shape word (%r)"
               % (row.get("base_nested_refused") if row else None,)) and ok
    got = PNDP.arm_entry("KEY", WITH_AS, "module", 7)
    ok = check(got["state"] == "refused"
               and got["reason"] == "with-as:body"
               and got["value"] is None,
               "AC-PNDP4 the entry law never resolves a with-as key (%r)"
               % (got,)) and ok
    leaves = row["leaves"].get("KEY") if row else None
    ok = check(not [item for item in (leaves or [])
                    if item["path"] == "if:2/body"],
               "AC-PNDP4 the with-as arm publishes no value leaf (%r)"
               % (leaves,)) and ok
    return ok


def ac_pndp5():
    """Every shipped answer is carried unchanged; the reading is read-only."""
    pairs = ((MIX_AGREE, "mix-agree"), (MIX_DEEP, "mix-deep"),
             (MIX_DIFF, "mix-diff"), (TRY_ELSE_AGREE, "try-else-agree"),
             (TRY_ELSE_EMPTY, "try-else-empty"), (TRY_FINALLY, "try-finally"),
             (WITH_AS, "with-as"), (NESTED_ONLY, "nested-only"),
             (NO_ELSE, "no-else"))
    ok = True
    for text, label in pairs:
        nested = nested_rows(text)[-1]
        base = base_rows(text)[-1]
        guard = guard_rows(text)[-1]
        mine = loop_rows(text)[-1]
        ok = check(mine["base_nested_followed"] == nested["followed"]
                   and mine["base_nested_refused"] == nested["refused"]
                   and mine["base_nested_arms"] == list(
                       nested.get("arms") or [])
                   and mine["base_followed"] == nested["base_followed"]
                   and mine["base_refused"] == nested["base_refused"]
                   and mine["base_arms"] == list(
                       nested.get("base_arms") or [])
                   and mine["base_guard_followed"]
                   == nested["base_guard_followed"]
                   and mine["base_guard_refused"]
                   == nested["base_guard_refused"],
                   "AC-PNDP5 all three shipped answers are carried on the "
                   "%s fixture" % (label,)) and ok
        ok = check(mine["base_followed"] == base["followed"]
                   and mine["base_refused"] == base["refused"]
                   and mine["base_guard_followed"] == guard["followed"]
                   and mine["base_guard_refused"] == guard["refused"],
                   "AC-PNDP5 the %s row matches the exhaustive and guard "
                   "faces directly" % (label,)) and ok
    nested_only = tail_row(NESTED_ONLY)
    ok = check(nested_only and nested_only["followed"].get("KEY") == "b"
               and nested_only["resolved_by_arm_mixed"] == [],
               "AC-PNDP5 a tree with no direct arm keeps the nested answer "
               "(%r)" % (nested_only.get("followed")
                         if nested_only else None,)) and ok
    no_else = tail_row(NO_ELSE)
    ok = check(no_else and no_else["followed"] == {}
               and no_else["refused"].get("KEY") == "incomplete:if:2",
               "AC-PNDP5 a chain with no final else is never resolved (%r)"
               % (no_else,)) and ok
    world = World()
    try:
        world.write("pndp_probe.py", PROBE_FIXTURE)
        before = tree_digest(world.path)
        digests = {}
        for path in (MODULE, NESTED_MODULE, EXH_MODULE, GUARD_MODULE,
                     RENDER_MODULE):
            digests[path] = digest(path)
        report = PNDP.audit(world.path, SM)
        ok = check(tree_digest(world.path) == before,
                   "AC-PNDP5 the probed tree is byte-identical after the "
                   "audit") and ok
        ok = check(all(digest(path) == value
                       for path, value in digests.items()),
                   "AC-PNDP5 the reading moved no shipped digest") and ok
        row = row_of(report, "pndp_probe.py")
        ok = check(row.get("verdict") == PNDP.COVERED,
                   "AC-PNDP5 the probe row still reads COVERED (%r)"
                   % (row.get("verdict"),)) and ok
        ok = check(row.get("arm_loops")
                   and row["arm_loops"][0]["followed"].get("KEY") == "b"
                   and row["arm_loops"][0]["resolved_by_arm_mixed"] == ["KEY"],
                   "AC-PNDP5 the row carries this face own folded loop (%r)"
                   % (row.get("arm_loops"),)) and ok
        ok = check(report["tool"] == PNDP.LABEL
                   and report["verdict"] == PNDP.SEAMS_ARM_MIXED_COVERED
                   and report["base_tool"] == PNCD.LABEL,
                   "AC-PNDP5 the report keeps the shipped base label (%r)"
                   % ((report["tool"], report["verdict"],
                       report.get("base_tool")),)) and ok
        refusal = PNDP.reading(os.path.join(world.path, "absent"), SM)
        ok = check(refusal.get("refusal") == PNDP.E_NO_ROOT
                   and refusal.get("probes") == [],
                   "AC-PNDP5 a missing root is refused, not raised (%r)"
                   % (refusal.get("refusal"),)) and ok
    finally:
        world.close()
    return ok


def ac_pndp6():
    """Pure ASCII, stdlib only, no clock, no network, wired once."""
    text = read_text(MODULE)
    suite = read_text(os.path.abspath(__file__))
    ok = check(all(ord(char) < 128 for char in text),
               "AC-PNDP6 the module source is pure ASCII")
    ok = check(all(ord(char) < 128 for char in suite),
               "AC-PNDP6 this suite source is pure ASCII") and ok
    imports = sorted(set(re.findall(r"(?m)^import ([A-Za-z_][A-Za-z0-9_]*)",
                                    text)))
    allowed = ("argparse", "ast", "hashlib", "json", "os", "sys")
    ok = check(not [name for name in imports if name not in allowed],
               "AC-PNDP6 only the allowed stdlib modules are imported (%s)"
               % (",".join(imports),)) and ok
    forbidden = ("time.time", "datetime", "socket", "urllib", "requests",
                 "http.client", "subprocess")
    ok = check(not [token for token in forbidden if token in text],
               "AC-PNDP6 no clock and no network token in the module") and ok
    registry = read_text(REGISTRY)
    ok = check(WIRED_LABEL in registry and WIRED_SUITE in registry,
               "AC-PNDP6 the face and its suite are wired into the registry "
               "exactly once") and ok
    ok = check(registry.count(WIRED_LABEL) == 1
               and registry.count(WIRED_SUITE) == 1,
               "AC-PNDP6 no duplicate registry row") and ok
    ok = check(PNDP.LABEL
               == "os-probe-seam-name-binding-nested-arm-mixed-scope",
               "AC-PNDP6 the reconcile label is the face own (%s)"
               % PNDP.LABEL) and ok
    ok = check(PNDP.SEAMS_ARM_MIXED_COVERED == "SEAMS-ARM-MIXED-COVERED"
               and PNDP.SEAMS_ARM_MIXED_STALE == "SEAMS-ARM-MIXED-STALE",
               "AC-PNDP6 the reading has its own verdict words (%s/%s)"
               % (PNDP.SEAMS_ARM_MIXED_COVERED,
                  PNDP.SEAMS_ARM_MIXED_STALE)) and ok
    ok = check(PNDP.REFUSED_WITH_AS == "with-as:%s"
               and PNDP.REFUSED_DISAGREE == "disagree:%s"
               and PNDP.REFUSED_PARTIAL == "partial:%s"
               and PNDP.REFUSED_INCOMPLETE == "incomplete:%s",
               "AC-PNDP6 the new refusal words are its own (%s/%s)"
               % (PNDP.REFUSED_WITH_AS, PNDP.REFUSED_DISAGREE)) and ok
    ok = check(PNCD.LABEL
               == "os-probe-seam-name-binding-nested-exhaustive-path",
               "AC-PNDP6 the shipped face it extends is still named") and ok
    return ok


def main():
    print("PROBE SEAM NAME BINDING NESTED ARM MIXED SCOPE SUITE "
          "(AC-PNDP1..AC-PNDP6)")
    results = [ac_pndp1(), ac_pndp2(), ac_pndp3(), ac_pndp4(), ac_pndp5(),
               ac_pndp6()]
    passed = len([item for item in results if item])
    print("SUITE %s %d/%d criteria green"
          % ("PASS" if passed == EXPECTED_CRITERIA else "FAIL",
             passed, EXPECTED_CRITERIA))
    return 0 if passed == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())