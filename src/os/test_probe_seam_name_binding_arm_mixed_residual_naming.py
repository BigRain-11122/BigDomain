"""AC-PNDQ1..AC-PNDQ6 suite for the arm-mixed residual naming face (R2553).

Criteria were pinned in state/queue/tech.md:589 at R2551 BEFORE this code
existed.

What this proves: MEASURED at R2551 on the shipped arm-mixed face own reader, a
plain `with ... as KEY` binding comes back as a refusal whose reason is
literally None, two SEQUENTIAL nested groups under one arm read
`grouped:<arm>` and never resolve even when every leaf agrees, and a direct arm
binding written through ONE module-level constant NAME reads
`non-literal:<arm>`. This face names the with-as binding, folds the sequential
groups together, follows one module-level constant name, and publishes both
values by full path when those groups disagree.

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

import probe_seam_name_binding_arm_mixed_residual_naming as PNDQ  # noqa: E402
import probe_seam_name_binding_nested_arm_mixed_scope as PNDP  # noqa: E402
import probe_seam_name_binding_nested_exhaustive_path as PNCD  # noqa: E402
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(
    BASE, "probe_seam_name_binding_arm_mixed_residual_naming.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
ARM_MODULE = os.path.join(
    BASE, "probe_seam_name_binding_nested_arm_mixed_scope.py")
NESTED_MODULE = os.path.join(
    BASE, "probe_seam_name_binding_nested_exhaustive_path.py")
RENDER_MODULE = os.path.join(SANDBOX, "suite_matrix.py")
WIRED_LABEL = '"os-probe-seam-name-binding-arm-mixed-residual-naming",'
WIRED_SUITE = '"test_probe_seam_name_binding_arm_mixed_residual_naming.py"),'

HELPER = "pndq_helper"

CONTAINER = ('D = {"a": {"b": ("%s",), "z": ("%s",)}}\n'
             % (HELPER, HELPER))

TAIL = 'for name in D["a"][KEY]:\n    pass\n'

WAS_MODULE = ('with open("x") as WK:\n'
              '    pass\n'
              + CONTAINER
              + 'if a1:\n'
                '    KEY = "b"\n'
              'else:\n'
              '    KEY = "b"\n'
              + TAIL)

WAS_FUNC = ('def f():\n'
            '    with open("x") as WK:\n'
            '        pass\n'
            '    ' + CONTAINER.replace("\n", "\n    ").rstrip() + '\n'
            '    if a1:\n'
            '        KEY = "b"\n'
            '    else:\n'
            '        KEY = "b"\n'
            '    for name in D["a"][KEY]:\n'
            '        pass\n')

SEQ_AGREE = (CONTAINER
             + 'if a1:\n'
               '    if a2:\n'
               '        KEY = "b"\n'
               '    else:\n'
               '        KEY = "b"\n'
               '    if a3:\n'
               '        KEY = "b"\n'
               '    else:\n'
               '        KEY = "b"\n'
               'else:\n'
               '    KEY = "b"\n'
             + TAIL)

SEQ_DIFF = (CONTAINER
            + 'if a1:\n'
              '    if a2:\n'
              '        KEY = "b"\n'
              '    else:\n'
              '        KEY = "b"\n'
              '    if a3:\n'
              '        KEY = "b"\n'
              '    else:\n'
              '        KEY = "z"\n'
              'else:\n'
              '    KEY = "b"\n'
            + TAIL)

CONST_OK = ('CONST = "b"\n'
            + CONTAINER
            + 'if a1:\n'
              '    KEY = CONST\n'
            'else:\n'
            '    KEY = CONST\n'
            + TAIL)

CONST_MIXED = ('AMB = "b"\n'
               'AMB = "z"\n'
               + CONTAINER
               + 'if a1:\n'
                 '    KEY = AMB\n'
               'else:\n'
               '    KEY = AMB\n'
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

MATCH_FIXTURE = (CONTAINER
                 + 'match x:\n'
                   '    case 1:\n'
                   '        KEY = "b"\n'
                   '    case _:\n'
                   '        KEY = "b"\n'
                 + TAIL)

PROBE_FIXTURE = ('import importlib\n'
                 '\n'
                 + CONTAINER
                 + 'if a1:\n'
                   '    if a2:\n'
                   '        KEY = "b"\n'
                   '    else:\n'
                   '        KEY = "b"\n'
                   '    if a3:\n'
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
    return PNDQ.residual_report(text)["loops"]


def arm_rows(text):
    return PNDP.arm_report(text)["loops"]


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
        self.path = tempfile.mkdtemp(prefix="pndq-suite-")
        seams = PNDQ.seam_names(SM)
        write_ascii(os.path.join(self.path, HELPER + ".py"),
                    helper_text(seams))

    def write(self, name, text):
        write_ascii(os.path.join(self.path, name), text)
        return name

    def close(self):
        shutil.rmtree(self.path, ignore_errors=True)


def ac_pndq1():
    """A plain with-as binding is NAMED, never refused with an empty reason."""
    row = tail_row(WAS_MODULE)
    ok = check(row and row["refused"].get("WK") == "with-as:module"
               and row["named_with_as"].get("WK") == "with-as:module",
               "AC-PNDQ1 a module-level with-as binding is NAMED (%r)"
               % (row.get("refused") if row else None,))
    ok = check(row and not [value for value in row["refused"].values()
                            if not value],
               "AC-PNDQ1 no refusal on the row carries an empty reason (%r)"
               % (row.get("refused"),)) and ok
    got = PNDQ.residual_entry("WK", WAS_MODULE, "module", 5)
    ok = check(got["state"] == "refused" and got["reason"] == "with-as:module"
               and got["with_as"] is True and got["value"] is None,
               "AC-PNDQ1 the entry law names the scope (%r)" % (got,)) and ok
    ok = check(got["base_arm_mixed_reason"] is None
               and got["base_arm_mixed_state"] == "refused",
               "AC-PNDQ1 the measured None from the shipped face is proven "
               "(%r)" % (got.get("base_arm_mixed_reason"),)) and ok
    func = tail_row(WAS_FUNC)
    ok = check(func and func["refused"].get("WK") == "with-as:function:f",
               "AC-PNDQ1 a function-level with-as binding names its scope "
               "(%r)" % (func.get("refused") if func else None,)) and ok
    return ok


def ac_pndq2():
    """Two sequential agreeing groups under one arm resolve to the literal."""
    row = tail_row(SEQ_AGREE)
    ok = check(row and row["followed"].get("KEY") == "b"
               and row["resolved_by_residual"] == ["KEY"],
               "AC-PNDQ2 two sequential agreeing groups resolve (%r)"
               % (row.get("followed") if row else None,))
    ok = check(row and row["base_arm_mixed_refused"].get("KEY")
               == "grouped:body",
               "AC-PNDQ2 the shipped arm-mixed face refused the same tree "
               "(%r)" % (row.get("base_arm_mixed_refused")
                         if row else None,)) and ok
    folded = row["groups_folded"].get("KEY") if row else None
    ok = check(folded == ["if:3", "if:7"],
               "AC-PNDQ2 both sequential groups are named (%r)"
               % (folded,)) and ok
    leaves = row["leaves"].get("KEY") if row else None
    ok = check(leaves and [item["value"] for item in leaves]
               == ["b", "b", "b", "b", "b"]
               and [item["path"] for item in leaves]
               == ["if:2/body>if:3/body", "if:2/body>if:3/else",
                   "if:2/body>if:7/body", "if:2/body>if:7/else",
                   "if:2/else"],
               "AC-PNDQ2 every leaf of both groups is published (%r)"
               % (leaves,)) and ok
    got = PNDQ.residual_entry("KEY", SEQ_AGREE, "module", 13)
    ok = check(got["state"] == "ok" and got["value"] == "b"
               and got["source"] == PNDQ.SOURCE_RESIDUAL
               and got["base_arm_mixed_reason"] == "grouped:body",
               "AC-PNDQ2 the entry law folds the groups (%r)" % (got,)) and ok
    return ok


def ac_pndq3():
    """A direct arm binding through one module constant name resolves."""
    row = tail_row(CONST_OK)
    ok = check(row and row["followed"].get("KEY") == "b"
               and row["resolved_by_residual"] == ["KEY"],
               "AC-PNDQ3 a direct binding through CONST resolves (%r)"
               % (row.get("followed") if row else None,))
    ok = check(row and row["base_arm_mixed_refused"].get("KEY")
               == "non-literal:body",
               "AC-PNDQ3 the shipped face used a shape word (%r)"
               % (row.get("base_arm_mixed_refused") if row else None,)) and ok
    got = PNDQ.residual_entry("KEY", CONST_OK, "module", 10)
    ok = check(got["state"] == "ok" and got["value"] == "b"
               and got["base_arm_mixed_reason"] == "non-literal:body",
               "AC-PNDQ3 the entry law follows ONE constant hop (%r)"
               % (got,)) and ok
    mixed = tail_row(CONST_MIXED)
    ok = check(mixed and mixed["refused"].get("KEY") == "name-mixed:AMB"
               and mixed["followed"] == {},
               "AC-PNDQ3 a name bound twice stays mixed (%r)"
               % (mixed.get("refused") if mixed else None,)) and ok
    ok = check(mixed and mixed["named_name_mixed"].get("KEY") == "AMB",
               "AC-PNDQ3 the ambiguous name is published by name (%r)"
               % (mixed.get("named_name_mixed") if mixed else None,)) and ok
    got = PNDQ.residual_entry("KEY", CONST_MIXED, "module", 12)
    ok = check(got["state"] == "refused"
               and got["reason"] == "name-mixed:AMB" and got["value"] is None,
               "AC-PNDQ3 the entry law never guesses a mixed name (%r)"
               % (got,)) and ok
    return ok


def ac_pndq4():
    """Disagreeing sequential groups publish both values and resolve nothing."""
    got = PNDQ.residual_entry("KEY", SEQ_DIFF, "module", 13)
    ok = check(got["state"] == "arms" and got["value"] is None
               and got["values"] == ["b", "z"],
               "AC-PNDQ4 disagreeing groups resolve nothing (%r)" % (got,))
    ok = check([item["path"] for item in got["leaves"]]
               == ["if:2/body>if:3/body", "if:2/body>if:3/else",
                   "if:2/body>if:7/body", "if:2/body>if:7/else",
                   "if:2/else"]
               and [item["value"] for item in got["leaves"]]
               == ["b", "b", "b", "z", "b"],
               "AC-PNDQ4 both values are published by full path (%r)"
               % (got["leaves"],)) and ok
    row = tail_row(SEQ_DIFF)
    ok = check(row and row["followed"] == {} and len(row["arms"]) == 1
               and row["arms"][0]["values"] == ["b", "z"],
               "AC-PNDQ4 the report refuses to pick a leaf (%r)"
               % (row.get("arms") if row else None,)) and ok
    ok = check(got["base_arm_mixed_reason"] == "grouped:body",
               "AC-PNDQ4 the shipped refusal is carried beside it (%r)"
               % (got.get("base_arm_mixed_reason"),)) and ok
    return ok


def ac_pndq5():
    """Every shipped answer is carried unchanged; the reading is read-only."""
    pairs = ((WAS_MODULE, "was-module"), (WAS_FUNC, "was-func"),
             (SEQ_AGREE, "seq-agree"), (SEQ_DIFF, "seq-diff"),
             (CONST_OK, "const-ok"), (CONST_MIXED, "const-mixed"),
             (NESTED_ONLY, "nested-only"), (MATCH_FIXTURE, "match"))
    ok = True
    for text, label in pairs:
        mine = tail_row(text)
        base = arm_rows(text)[-1]
        ok = check(mine["base_arm_mixed_followed"] == base["followed"]
                   and mine["base_arm_mixed_refused"] == base["refused"]
                   and mine["base_arm_mixed_arms"]
                   == list(base.get("arms") or []),
                   "AC-PNDQ5 the arm-mixed answer is carried on %s"
                   % (label,)) and ok
        ok = check(mine["base_followed"] == base["base_followed"]
                   and mine["base_refused"] == base["base_refused"]
                   and mine["base_guard_followed"]
                   == base["base_guard_followed"],
                   "AC-PNDQ5 the guard and exhaustive answers still ride on %s"
                   % (label,)) and ok
    shipped_ok = PNDP.arm_entry("KEY", NESTED_ONLY, "module", 9)
    carried = PNDQ.residual_entry("KEY", NESTED_ONLY, "module", 9)
    ok = check(shipped_ok["state"] == "ok" and carried["state"] == "ok"
               and carried["value"] == shipped_ok["value"]
               and carried["source"] == shipped_ok["source"],
               "AC-PNDQ5 a resolved tree is returned UNCHANGED (%r)"
               % ((carried["state"], carried["value"],
                   carried["source"]),)) and ok
    shipped_bad = PNDP.arm_entry("KEY", MATCH_FIXTURE, "module", 7)
    kept = PNDQ.residual_entry("KEY", MATCH_FIXTURE, "module", 7)
    ok = check(kept["state"] == shipped_bad["state"]
               and kept["reason"] == shipped_bad["reason"]
               == "match:2-cases",
               "AC-PNDQ5 an untouched refusal keeps its own word (%r)"
               % (kept["reason"],)) and ok
    world = World()
    try:
        world.write("pndq_probe.py", PROBE_FIXTURE)
        before = tree_digest(world.path)
        digests = {}
        for path in (MODULE, ARM_MODULE, NESTED_MODULE, RENDER_MODULE):
            digests[path] = digest(path)
        report = PNDQ.audit(world.path, SM)
        ok = check(tree_digest(world.path) == before,
                   "AC-PNDQ5 the probed tree is byte-identical after the "
                   "audit") and ok
        ok = check(all(digest(path) == value
                       for path, value in digests.items()),
                   "AC-PNDQ5 the reading moved no shipped digest") and ok
        row = row_of(report, "pndq_probe.py")
        ok = check(row.get("verdict") == PNDQ.COVERED,
                   "AC-PNDQ5 the probe row still reads COVERED (%r)"
                   % (row.get("verdict"),)) and ok
        ok = check(row.get("residual_loops")
                   and row["residual_loops"][0]["followed"].get("KEY") == "b"
                   and row["residual_loops"][0]["resolved_by_residual"]
                   == ["KEY"],
                   "AC-PNDQ5 the row carries this face own folded loop (%r)"
                   % (row.get("residual_loops"),)) and ok
        ok = check(report["tool"] == PNDQ.LABEL
                   and report["verdict"] == PNDQ.SEAMS_RESIDUAL_COVERED
                   and report["base_tool"] == PNDP.LABEL,
                   "AC-PNDQ5 the report keeps the shipped base label (%r)"
                   % ((report["tool"], report["verdict"],
                       report.get("base_tool")),)) and ok
        refusal = PNDQ.reading(os.path.join(world.path, "absent"), SM)
        ok = check(refusal.get("refusal") == PNDQ.E_NO_ROOT
                   and refusal.get("probes") == [],
                   "AC-PNDQ5 a missing root is refused, not raised (%r)"
                   % (refusal.get("refusal"),)) and ok
    finally:
        world.close()
    return ok


def ac_pndq6():
    """Pure ASCII, stdlib only, no clock, no network, wired once."""
    text = read_text(MODULE)
    suite = read_text(os.path.abspath(__file__))
    ok = check(all(ord(char) < 128 for char in text),
               "AC-PNDQ6 the module source is pure ASCII")
    ok = check(all(ord(char) < 128 for char in suite),
               "AC-PNDQ6 this suite source is pure ASCII") and ok
    imports = sorted(set(re.findall(r"(?m)^import ([A-Za-z_][A-Za-z0-9_]*)",
                                    text)))
    allowed = ("argparse", "ast", "hashlib", "json", "os", "sys")
    ok = check(not [name for name in imports if name not in allowed],
               "AC-PNDQ6 only the allowed stdlib modules are imported (%s)"
               % (",".join(imports),)) and ok
    forbidden = ("time.time", "datetime", "socket", "urllib", "requests",
                 "http.client", "subprocess")
    ok = check(not [token for token in forbidden if token in text],
               "AC-PNDQ6 no clock and no network token in the module") and ok
    registry = read_text(REGISTRY)
    ok = check(WIRED_LABEL in registry and WIRED_SUITE in registry,
               "AC-PNDQ6 the face and its suite are wired into the registry") \
        and ok
    ok = check(registry.count(WIRED_LABEL) == 1
               and registry.count(WIRED_SUITE) == 1,
               "AC-PNDQ6 no duplicate registry row") and ok
    ok = check(PNDQ.LABEL
               == "os-probe-seam-name-binding-arm-mixed-residual-naming",
               "AC-PNDQ6 the reconcile label is the face own (%s)"
               % PNDQ.LABEL) and ok
    ok = check(PNDQ.SEAMS_RESIDUAL_COVERED == "SEAMS-RESIDUAL-COVERED"
               and PNDQ.SEAMS_RESIDUAL_STALE == "SEAMS-RESIDUAL-STALE",
               "AC-PNDQ6 the reading has its own verdict words (%s/%s)"
               % (PNDQ.SEAMS_RESIDUAL_COVERED,
                  PNDQ.SEAMS_RESIDUAL_STALE)) and ok
    ok = check(PNDQ.REFUSED_WITH_AS == "with-as:%s"
               and PNDQ.REFUSED_NAME_MIXED == "name-mixed:%s"
               and PNDQ.REFUSED_DISAGREE == "disagree:%s",
               "AC-PNDQ6 the new refusal words are its own (%s/%s/%s)"
               % (PNDQ.REFUSED_WITH_AS, PNDQ.REFUSED_NAME_MIXED,
                  PNDQ.REFUSED_DISAGREE)) and ok
    ok = check(PNDP.LABEL
               == "os-probe-seam-name-binding-nested-arm-mixed-scope",
               "AC-PNDQ6 the shipped face it extends is still named") and ok
    return ok


def main():
    print("PROBE SEAM NAME BINDING ARM MIXED RESIDUAL NAMING SUITE "
          "(AC-PNDQ1..AC-PNDQ6)")
    results = [ac_pndq1(), ac_pndq2(), ac_pndq3(), ac_pndq4(), ac_pndq5(),
               ac_pndq6()]
    passed = len([item for item in results if item])
    print("SUITE %s %d/%d criteria green"
          % ("PASS" if passed == EXPECTED_CRITERIA else "FAIL",
             passed, EXPECTED_CRITERIA))
    return 0 if passed == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())