"""AC-PNCD1..AC-PNCD6 suite for the nested exhaustive path face (R2549).

Criteria were pinned in state/queue/tech.md:585 at R2547 BEFORE this code
existed.

What this proves: MEASURED at R2547 on the shipped exhaustive face own reader,
a nested if that agrees on every leaf reads as TWO groups and resolves
nothing, an arm that binds nothing is still published as an arm binding, and a
loop inside an arm keeps the shipped loop guard. This face folds a nested
guard tree whose every leaf agrees into the ROOT group own coverage, and every
case is checked on BOTH shipped readers.

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

import probe_seam_name_binding_nested_exhaustive_path as PNCD  # noqa: E402
import probe_seam_name_binding_control_flow_guard_exhaustive as PNCT  # noqa: E402
import probe_seam_name_binding_control_flow_guard_scope as PNCG  # noqa: E402
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(
    BASE, "probe_seam_name_binding_nested_exhaustive_path.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
EXH_MODULE = os.path.join(
    BASE, "probe_seam_name_binding_control_flow_guard_exhaustive.py")
GUARD_MODULE = os.path.join(
    BASE, "probe_seam_name_binding_control_flow_guard_scope.py")
RENDER_MODULE = os.path.join(SANDBOX, "suite_matrix.py")
WIRED_LABEL = '"os-probe-seam-name-binding-nested-exhaustive-path",'
WIRED_SUITE = (
    '"test_probe_seam_name_binding_nested_exhaustive_path.py"),')

HELPER = "pncd_helper"

CONTAINER = ('D = {"a": {"b": ("%s",), "z": ("%s",)}}\n'
             % (HELPER, HELPER))

TAIL = 'for name in D["a"][KEY]:\n    pass\n'

NESTED_AGREE = (CONTAINER
                + 'if a1:\n'
                  '    if a2:\n'
                  '        KEY = "b"\n'
                  '    else:\n'
                  '        KEY = "b"\n'
                  'else:\n'
                  '    KEY = "b"\n'
                + TAIL)

NESTED_PARTIAL = (CONTAINER
                  + 'if a1:\n'
                    '    if a2:\n'
                    '        KEY = "b"\n'
                    '    else:\n'
                    '        KEY = "b"\n'
                    'else:\n'
                    '    pass\n'
                  + TAIL)

NESTED_LOOP = (CONTAINER
               + 'if a1:\n'
                 '    KEY = "b"\n'
                 'else:\n'
                 '    for _x in ("b",):\n'
                 '        KEY = "b"\n'
               + TAIL)

NESTED_DIFF = (CONTAINER
               + 'if a1:\n'
                 '    if a2:\n'
                 '        KEY = "b"\n'
                 '    else:\n'
                 '        KEY = "z"\n'
                 'else:\n'
                 '    KEY = "b"\n'
               + TAIL)

DEEP_AGREE = (CONTAINER
              + 'if a1:\n'
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

PLAIN = (CONTAINER
         + 'KEY = "b"\n'
           'if cond:\n'
           '    KEY = "z"\n'
         + TAIL)

NO_ELSE = (CONTAINER
           + 'if a1:\n'
             '    KEY = "b"\n'
           + TAIL)

PROBE_FIXTURE = ('import importlib\n'
                 '\n'
                 + CONTAINER
                 + 'if a1:\n'
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
    return PNCD.nested_report(text)["loops"]


def tail_row(text):
    rows = loop_rows(text)
    return rows[-1] if rows else {}


def base_rows(text):
    return PNCT.exhaustive_report(text)["loops"]


def guard_rows(text):
    return PNCG.guard_report(text)["loops"]


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
        self.path = tempfile.mkdtemp(prefix="pncd-suite-")
        seams = PNCD.seam_names(SM)
        write_ascii(os.path.join(self.path, HELPER + ".py"),
                    helper_text(seams))

    def write(self, name, text):
        write_ascii(os.path.join(self.path, name), text)
        return name

    def close(self):
        shutil.rmtree(self.path, ignore_errors=True)


def ac_pncd1():
    """A nested if that agrees on every leaf resolves to that value."""
    row = tail_row(NESTED_AGREE)
    ok = check(row and row["followed"].get("KEY") == "b"
               and row["resolved_by_nested"] == ["KEY"],
               "AC-PNCD1 a nested agreeing tree resolves (%r)" % (row,))
    ok = check(row and row["base_refused"].get("KEY")
               == "guarded:if:2>if:3" and row["base_followed"] == {},
               "AC-PNCD1 the exhaustive face refused the same tree (%r)"
               % (row.get("base_refused") if row else None,)) and ok
    base = base_rows(NESTED_AGREE)[0]
    ok = check([item["group"] for item in base["exh_groups"]]
               == ["if:3", "if:2"],
               "AC-PNCD1 the exhaustive face published TWO groups (%r)"
               % ([item["group"] for item in base["exh_groups"]],)) and ok
    got = PNCD.nested_entry("KEY", NESTED_AGREE, "module", 9)
    ok = check(got["state"] == "ok" and got["value"] == "b"
               and got["source"] == PNCD.SOURCE_NESTED
               and got["root"] == "if:2",
               "AC-PNCD1 the entry law folds to the ROOT group (%r)"
               % (got,)) and ok
    leaves = [item["path"] for item in got["leaves"]]
    ok = check(leaves == ["if:2/body>if:3/body", "if:2/body>if:3/else",
                          "if:2/else"],
               "AC-PNCD1 every leaf path is published (%r)" % (leaves,)) and ok
    deep = tail_row(DEEP_AGREE)
    ok = check(deep and deep["followed"].get("KEY") == "b",
               "AC-PNCD1 a three-deep agreeing tree resolves (%r)"
               % (deep,)) and ok
    return ok


def ac_pncd2():
    """An arm that binds nothing is NAMED partial:<arm> and never resolved."""
    row = tail_row(NESTED_PARTIAL)
    ok = check(row and row["refused"].get("KEY") == "partial:else"
               and row["followed"] == {},
               "AC-PNCD2 the empty arm is named partial:else (%r)" % (row,))
    ok = check(row and row["partial"].get("KEY") == "else",
               "AC-PNCD2 the arm is published as a fact (%r)"
               % (row["partial"] if row else None,)) and ok
    got = PNCD.nested_entry("KEY", NESTED_PARTIAL, "module", 9)
    ok = check(got["state"] == "refused"
               and got["reason"] == "partial:else"
               and got["value"] is None,
               "AC-PNCD2 the entry law never resolves it (%r)" % (got,)) and ok
    base = base_rows(NESTED_PARTIAL)[0]
    ok = check(base["followed"].get("KEY") == "b",
               "AC-PNCD2 the exhaustive face resolved a value the outer arm "
               "does not prove (%r)" % (base["followed"],)) and ok
    ok = check(len(got["leaves"]) == 3
               and got["leaves"][-1]["values"] == [],
               "AC-PNCD2 the empty leaf carries no value (%r)"
               % (got["leaves"],)) and ok
    return ok


def ac_pncd3():
    """A loop inside an arm is NAMED loop:<line> and never folded."""
    row = tail_row(NESTED_LOOP)
    ok = check(row and row["refused"].get("KEY") == "loop:5"
               and row["followed"] == {},
               "AC-PNCD3 the loop under an arm is named loop:5 (%r)"
               % (row,))
    ok = check(row and row["loops"].get("KEY") == "loop:5",
               "AC-PNCD3 the loop is published as a fact (%r)"
               % (row["loops"] if row else None,)) and ok
    got = PNCD.nested_entry("KEY", NESTED_LOOP, "module", 7)
    ok = check(got["state"] == "refused"
               and got["reason"] == "loop:5"
               and got["value"] is None,
               "AC-PNCD3 the entry law never folds it (%r)" % (got,)) and ok
    base = base_rows(NESTED_LOOP)[-1]
    ok = check(base["followed"].get("KEY") == "b",
               "AC-PNCD3 the exhaustive face resolved it instead (%r)"
               % (base["followed"],)) and ok
    rows = loop_rows(NESTED_LOOP)
    ok = check(len(rows) == 2 and rows[0]["line"] == 5
               and rows[0]["followed"] == {},
               "AC-PNCD3 the inner loop keeps its own row (%r)"
               % ([item["line"] for item in rows],)) and ok
    return ok


def ac_pncd4():
    """A nested tree whose leaves disagree publishes every leaf by its path."""
    row = tail_row(NESTED_DIFF)
    ok = check(row and row["followed"] == {}
               and len(row["arms"]) == 1,
               "AC-PNCD4 a disagreeing tree resolves nothing (%r)" % (row,))
    arms = row["arms"][0]["arms"] if row and row["arms"] else None
    ok = check(isinstance(arms, list) and len(arms) == 2
               and arms[0]["state"] == "arms"
               and arms[0]["values"] == ["b", "z"]
               and arms[1]["state"] == "ok",
               "AC-PNCD4 the fold publishes BOTH values (%r)" % (arms,)) and ok
    leaves = row["leaves"].get("KEY") if row else None
    ok = check(leaves and [item["path"] for item in leaves]
               == ["if:2/body>if:3/body", "if:2/body>if:3/else", "if:2/else"]
               and [item["value"] for item in leaves] == ["b", "z", "b"],
               "AC-PNCD4 every leaf is published by its full path (%r)"
               % (leaves,)) and ok
    got = PNCD.nested_entry("KEY", NESTED_DIFF, "module", 9)
    ok = check(got["state"] == "arms"
               and got["reason"] == PNCD.REFUSED_NESTED_ARMS
               and got["value"] is None,
               "AC-PNCD4 the entry law refuses to pick a leaf (%r)"
               % (got,)) and ok
    base = base_rows(NESTED_DIFF)[0]
    ok = check(base["followed"] == {} and len(base["arms"]) == 1,
               "AC-PNCD4 the exhaustive face also refused to pick (%r)"
               % (base,)) and ok
    return ok


def ac_pncd5():
    """Every shipped answer is carried unchanged; the reading is read-only."""
    pairs = ((NESTED_AGREE, "nested-agree"), (NESTED_PARTIAL, "nested-partial"),
             (NESTED_LOOP, "nested-loop"), (NESTED_DIFF, "nested-diff"),
             (PLAIN, "plain"), (NO_ELSE, "no-else"))
    ok = True
    for text, label in pairs:
        base = base_rows(text)[-1]
        guard = guard_rows(text)[-1]
        mine = loop_rows(text)[-1]
        ok = check(mine["base_followed"] == base["followed"]
                   and mine["base_refused"] == base["refused"]
                   and mine["base_arms"] == list(base.get("arms") or [])
                   and mine["base_guard_followed"] == guard["followed"]
                   and mine["base_guard_refused"] == guard["refused"],
                   "AC-PNCD5 both shipped answers are carried unchanged on the "
                   "%s fixture" % (label,)) and ok
    plain = tail_row(PLAIN)
    ok = check(plain and plain["followed"].get("KEY") == "b"
               and plain["resolved_by_nested"] == [],
               "AC-PNCD5 an unconditional binding keeps the shipped answer "
               "(%r)" % (plain,)) and ok
    no_else = tail_row(NO_ELSE)
    ok = check(no_else and no_else["followed"] == {}
               and no_else["refused"].get("KEY") == "incomplete:if:2",
               "AC-PNCD5 a chain with no final else is never resolved (%r)"
               % (no_else,)) and ok
    world = World()
    try:
        world.write("pncd_probe.py", PROBE_FIXTURE)
        before = tree_digest(world.path)
        module_before = digest(MODULE)
        exh_before = digest(EXH_MODULE)
        guard_before = digest(GUARD_MODULE)
        render_before = digest(RENDER_MODULE)
        report = PNCD.audit(world.path, SM)
        ok = check(tree_digest(world.path) == before,
                   "AC-PNCD5 the probed tree is byte-identical after the "
                   "audit") and ok
        ok = check(digest(MODULE) == module_before
                   and digest(EXH_MODULE) == exh_before
                   and digest(GUARD_MODULE) == guard_before
                   and digest(RENDER_MODULE) == render_before,
                   "AC-PNCD5 the reading moved no shipped digest") and ok
        row = row_of(report, "pncd_probe.py")
        ok = check(row.get("verdict") == PNCD.COVERED,
                   "AC-PNCD5 the probe row still reads COVERED (%r)"
                   % (row.get("verdict"),)) and ok
        ok = check(row.get("nested_loops")
                   and row["nested_loops"][0]["followed"].get("KEY") == "b",
                   "AC-PNCD5 the row carries this face own folded loop (%r)"
                   % (row.get("nested_loops"),)) and ok
        ok = check(report["tool"] == PNCD.LABEL
                   and report["verdict"] == PNCD.SEAMS_NESTED_COVERED
                   and report["base_tool"] == PNCT.LABEL,
                   "AC-PNCD5 the report keeps the shipped base label (%r)"
                   % ((report["tool"], report["verdict"],
                       report.get("base_tool")),)) and ok
        refusal = PNCD.reading(os.path.join(world.path, "absent"), SM)
        ok = check(refusal.get("refusal") == PNCD.E_NO_ROOT
                   and refusal.get("probes") == [],
                   "AC-PNCD5 a missing root is refused, not raised (%r)"
                   % (refusal.get("refusal"),)) and ok
    finally:
        world.close()
    return ok


def ac_pncd6():
    """Pure ASCII, stdlib only, no clock, no network, wired once."""
    text = read_text(MODULE)
    suite = read_text(os.path.abspath(__file__))
    ok = check(all(ord(char) < 128 for char in text),
               "AC-PNCD6 the module source is pure ASCII")
    ok = check(all(ord(char) < 128 for char in suite),
               "AC-PNCD6 this suite source is pure ASCII") and ok
    imports = sorted(set(re.findall(r"(?m)^import ([A-Za-z_][A-Za-z0-9_]*)",
                                    text)))
    allowed = ("argparse", "ast", "hashlib", "json", "os", "sys")
    ok = check(not [name for name in imports if name not in allowed],
               "AC-PNCD6 only the allowed stdlib modules are imported (%s)"
               % (",".join(imports),)) and ok
    forbidden = ("time.time", "datetime", "socket", "urllib", "requests",
                 "http.client", "subprocess")
    ok = check(not [token for token in forbidden if token in text],
               "AC-PNCD6 no clock and no network token in the module") and ok
    registry = read_text(REGISTRY)
    ok = check(WIRED_LABEL in registry and WIRED_SUITE in registry,
               "AC-PNCD6 the face and its suite are wired into the registry "
               "exactly once") and ok
    ok = check(registry.count(WIRED_LABEL) == 1
               and registry.count(WIRED_SUITE) == 1,
               "AC-PNCD6 no duplicate registry row") and ok
    ok = check(PNCD.LABEL
               == "os-probe-seam-name-binding-nested-exhaustive-path",
               "AC-PNCD6 the reconcile label is the face own (%s)"
               % PNCD.LABEL) and ok
    ok = check(PNCD.SEAMS_NESTED_COVERED == "SEAMS-NESTED-COVERED"
               and PNCD.SEAMS_NESTED_STALE == "SEAMS-NESTED-STALE",
               "AC-PNCD6 the reading has its own verdict words (%s/%s)"
               % (PNCD.SEAMS_NESTED_COVERED,
                  PNCD.SEAMS_NESTED_STALE)) and ok
    ok = check(PNCD.REFUSED_PARTIAL == "partial:%s"
               and PNCD.REFUSED_LOOP == "loop:%d"
               and PNCD.REFUSED_NESTED_ARMS == "nested-arms"
               and PNCD.REFUSED_INCOMPLETE == "incomplete:%s",
               "AC-PNCD6 the new refusal words are its own (%s/%s/%s)"
               % (PNCD.REFUSED_PARTIAL, PNCD.REFUSED_NESTED_ARMS,
                  PNCD.REFUSED_INCOMPLETE)) and ok
    ok = check(PNCT.LABEL
               == "os-probe-seam-name-binding-control-flow-guard-exhaustive",
               "AC-PNCD6 the shipped face it extends is still named") and ok
    return ok


def main():
    print("PROBE SEAM NAME BINDING NESTED EXHAUSTIVE PATH SUITE "
          "(AC-PNCD1..AC-PNCD6)")
    results = [ac_pncd1(), ac_pncd2(), ac_pncd3(), ac_pncd4(), ac_pncd5(),
               ac_pncd6()]
    passed = len([item for item in results if item])
    print("SUITE %s %d/%d criteria green"
          % ("PASS" if passed == EXPECTED_CRITERIA else "FAIL",
             passed, EXPECTED_CRITERIA))
    return 0 if passed == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())