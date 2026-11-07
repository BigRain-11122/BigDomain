"""AC-PNCT1..AC-PNCT6 suite for the exhaustive-path binding face (R2547).

Criteria were pinned in state/queue/tech.md:583 at R2545 BEFORE this code
existed.

What this proves: MEASURED at R2545 on the shipped guard face own reader, an
if/elif/else chain covering every path read as exclusive arms so the elif own
value never appeared, a match statement was not collected at all, a
conditional expression read the bare shape word "shape", and a try/except
whose two arms bound the SAME literal was refused. This face answers all four
on top of the shipped law, and every case is checked on BOTH readers.

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

import probe_seam_name_binding_control_flow_guard_exhaustive as PNCT  # noqa: E402
import probe_seam_name_binding_control_flow_guard_scope as PNCG  # noqa: E402
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(
    BASE, "probe_seam_name_binding_control_flow_guard_exhaustive.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
BASE_MODULE = os.path.join(
    BASE, "probe_seam_name_binding_control_flow_guard_scope.py")
RENDER_MODULE = os.path.join(SANDBOX, "suite_matrix.py")
WIRED_LABEL = '"os-probe-seam-name-binding-control-flow-guard-exhaustive",'
WIRED_SUITE = (
    '"test_probe_seam_name_binding_control_flow_guard_exhaustive.py"),')

HELPER = "pnct_helper"

CONTAINER = ('D = {"a": {"b": ("%s",), "z": ("%s",), "c": ("%s",)}}\n'
             % (HELPER, HELPER, HELPER))

TAIL = 'for name in D["a"][KEY]:\n    pass\n'

CHAIN_AGREE = (CONTAINER
               + 'if a1:\n'
                 '    KEY = "b"\n'
                 'elif a2:\n'
                 '    KEY = "b"\n'
                 'else:\n'
                 '    KEY = "b"\n'
               + TAIL)

CHAIN_DIFF = (CONTAINER
              + 'if a1:\n'
                '    KEY = "b"\n'
                'elif a2:\n'
                '    KEY = "z"\n'
                'else:\n'
                '    KEY = "b"\n'
              + TAIL)

CHAIN_NO_ELSE = (CONTAINER
                 + 'if a1:\n'
                   '    KEY = "b"\n'
                 + TAIL)

TRY_AGREE = (CONTAINER
             + 'try:\n'
               '    KEY = "b"\n'
               'except Exception:\n'
               '    KEY = "b"\n'
             + TAIL)

TRY_DIFF = (CONTAINER
            + 'try:\n'
              '    KEY = "b"\n'
              'except Exception:\n'
              '    KEY = "z"\n'
            + TAIL)

TRY_ELSE = (CONTAINER
            + 'try:\n'
              '    KEY = "b"\n'
              'except Exception:\n'
              '    KEY = "b"\n'
              'else:\n'
              '    KEY = "b"\n'
            + TAIL)

TRY_TWO_HANDLERS = (CONTAINER
                    + 'try:\n'
                      '    KEY = "b"\n'
                      'except ValueError:\n'
                      '    KEY = "b"\n'
                      'except KeyError:\n'
                      '    KEY = "b"\n'
                    + TAIL)

COND_AGREE = (CONTAINER
              + 'KEY = "b" if cond else "b"\n'
              + TAIL)

COND_DIFF = (CONTAINER
             + 'KEY = "b" if cond else "z"\n'
             + TAIL)

COND_SHAPE = (CONTAINER
              + 'KEY = "{}".format(x) if cond else "b"\n'
              + TAIL)

MATCH_FIXTURE = (CONTAINER
                 + 'match kind:\n'
                   '    case 1:\n'
                   '        KEY = "b"\n'
                   '    case _:\n'
                   '        KEY = "z"\n'
                 + TAIL)

PLAIN = (CONTAINER
         + 'KEY = "b"\n'
           'if cond:\n'
           '    KEY = "z"\n'
         + TAIL)

TWO_ARM_AGREE = (CONTAINER
                 + 'if cond:\n'
                   '    KEY = "b"\n'
                   'else:\n'
                   '    KEY = "b"\n'
                 + TAIL)

PROBE_FIXTURE = ('import importlib\n'
                 '\n'
                 + CONTAINER
                 + 'if a1:\n'
                   '    KEY = "b"\n'
                   'elif a2:\n'
                   '    KEY = "b"\n'
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
    return PNCT.exhaustive_report(text)["loops"]


def base_rows(text):
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
        self.path = tempfile.mkdtemp(prefix="pnct-suite-")
        seams = PNCT.seam_names(SM)
        write_ascii(os.path.join(self.path, HELPER + ".py"),
                    helper_text(seams))

    def write(self, name, text):
        write_ascii(os.path.join(self.path, name), text)
        return name

    def close(self):
        shutil.rmtree(self.path, ignore_errors=True)


def ac_pnct1():
    """An agreeing if/elif/else chain resolves; a differing one publishes all."""
    rows = loop_rows(CHAIN_AGREE)
    ok = check(len(rows) == 1
               and rows[0]["followed"].get("KEY") == "b"
               and rows[0]["resolved_by_exhaustive"] == ["KEY"],
               "AC-PNCT1 an agreeing if/elif/else chain resolves (%r)"
               % (rows,))
    ok = check(rows and rows[0]["base_refused"].get("KEY")
               == "guarded:if:2",
               "AC-PNCT1 the shipped guard face refused the same chain (%r)"
               % (rows[0]["base_refused"] if rows else None,)) and ok
    ok = check(rows and [group["group"] for group in rows[0]["exh_groups"]]
               == ["if:2"]
               and rows[0]["exh_groups"][0]["exhaustive"] is True
               and rows[0]["exh_groups"][0]["covered"] is True,
               "AC-PNCT1 the chain is one exhaustive covered group (%r)"
               % (rows[0]["exh_groups"] if rows else None,)) and ok
    got = PNCT.exhaustive_entry("KEY", CHAIN_AGREE, "module", 8)
    ok = check(got["state"] == "ok" and got["value"] == "b"
               and got["source"] == PNCT.SOURCE_EXHAUSTIVE,
               "AC-PNCT1 the entry law resolves the chain (%r)" % (got,)) and ok
    diff = loop_rows(CHAIN_DIFF)
    ok = check(len(diff) == 1 and diff[0]["followed"] == {}
               and len(diff[0]["arms"]) == 1
               and diff[0]["arms"][0]["name"] == "KEY",
               "AC-PNCT1 a chain with two values resolves nothing (%r)"
               % (diff,)) and ok
    arms = diff[0]["arms"][0]["arms"] if diff else []
    ok = check([item["arm"] for item in arms] == ["body", "elif1", "else"]
               and [item["value"] for item in arms] == ["b", "z", "b"],
               "AC-PNCT1 every arm is published by name (%r)" % (arms,)) and ok
    base = base_rows(CHAIN_DIFF)
    ok = check(base and base[0]["refused"].get("KEY") is None
               and [item["arm"] for item in base[0]["arms"][0]["arms"]]
               == ["body", "else"]
               and base[0]["arms"][0]["arms"][0]["group"] == "if:4",
               "AC-PNCT1 the shipped face published only the INNER pair of the "
               "chain and dropped the first arm (%r)"
               % (base[0]["arms"] if base else None,)) and ok
    no_else = loop_rows(CHAIN_NO_ELSE)
    ok = check(len(no_else) == 1
               and no_else[0]["refused"].get("KEY") == "guarded:if:2"
               and no_else[0]["exh_groups"][0]["exhaustive"] is False,
               "AC-PNCT1 a chain without a final else is never resolved (%r)"
               % (no_else,)) and ok
    return ok


def ac_pnct2():
    """An agreeing try/except resolves; differing arms stay named, not resolved."""
    rows = loop_rows(TRY_AGREE)
    ok = check(len(rows) == 1 and rows[0]["followed"].get("KEY") == "b"
               and rows[0]["resolved_by_exhaustive"] == ["KEY"],
               "AC-PNCT2 two agreeing try arms resolve (%r)" % (rows,))
    ok = check(rows and rows[0]["base_refused"].get("KEY") == "guarded:try:2",
               "AC-PNCT2 the shipped face refused the same-literal try (%r)"
               % (rows[0]["base_refused"] if rows else None,)) and ok
    got = PNCT.exhaustive_entry("KEY", TRY_AGREE, "module", 8)
    ok = check(got["state"] == "ok" and got["value"] == "b"
               and got["source"] == PNCT.SOURCE_EXHAUSTIVE,
               "AC-PNCT2 the entry law resolves the agreeing try (%r)"
               % (got,)) and ok
    diff = loop_rows(TRY_DIFF)
    ok = check(len(diff) == 1 and diff[0]["followed"] == {}
               and len(diff[0]["arms"]) == 1,
               "AC-PNCT2 differing try arms resolve nothing (%r)"
               % (diff,)) and ok
    arms = diff[0]["arms"][0]["arms"] if diff else []
    ok = check([(item["arm"], item["value"]) for item in arms]
               == [("body", "b"), ("except0", "z")],
               "AC-PNCT2 both try arms are named (%r)" % (arms,)) and ok
    base = base_rows(TRY_DIFF)
    ok = check(base and base[0]["arms"] and base[0]["arms"][0]["arms"]
               == diff[0]["arms"][0]["arms"],
               "AC-PNCT2 the shipped arms are carried unchanged (%r)"
               % (diff[0]["base_arms"] if diff else None,)) and ok
    ok = check(diff and diff[0]["base_arms"] == base[0]["arms"],
               "AC-PNCT2 the row keeps the shipped arm list (%r)"
               % (diff[0]["base_arms"] if diff else None,)) and ok
    with_else = loop_rows(TRY_ELSE)
    two_handlers = loop_rows(TRY_TWO_HANDLERS)
    ok = check(len(with_else) == 1
               and with_else[0]["followed"] == {}
               and with_else[0]["exh_groups"][0]["exhaustive"] is False,
               "AC-PNCT2 a try with an else arm is never resolved (%r)"
               % (with_else,)) and ok
    ok = check(len(two_handlers) == 1
               and two_handlers[0]["followed"] == {}
               and two_handlers[0]["exh_groups"][0]["exhaustive"] is False,
               "AC-PNCT2 a try with two handlers is never resolved (%r)"
               % (two_handlers,)) and ok
    return ok


def ac_pnct3():
    """A conditional expression publishes both operands, resolving only if equal."""
    diff = loop_rows(COND_DIFF)
    ok = check(len(diff) == 1 and diff[0]["followed"] == {}
               and diff[0]["refused"].get("KEY")
               == PNCT.REFUSED_CONDEXPR % ("b", "z"),
               "AC-PNCT3 a differing conditional expression is named by its "
               "operands (%r)" % (diff,))
    operands = diff[0]["operands"].get("KEY") if diff else None
    ok = check(operands and [(item["kind"], item["value"]) for item in operands]
               == [("str", "b"), ("str", "z")],
               "AC-PNCT3 both operands are published (%r)" % (operands,)) and ok
    base = base_rows(COND_DIFF)
    ok = check(base and base[0]["refused"].get("KEY") == "shape",
               "AC-PNCT3 the shipped face read the bare shape word (%r)"
               % (base[0]["refused"] if base else None,)) and ok
    agree = loop_rows(COND_AGREE)
    ok = check(len(agree) == 1 and agree[0]["followed"].get("KEY") == "b"
               and agree[0]["resolved_by_exhaustive"] == ["KEY"],
               "AC-PNCT3 an agreeing conditional expression resolves (%r)"
               % (agree,)) and ok
    shaped = loop_rows(COND_SHAPE)
    ok = check(len(shaped) == 1 and shaped[0]["followed"] == {}
               and shaped[0]["refused"].get("KEY")
               == PNCT.REFUSED_CONDEXPR % ("format", "b"),
               "AC-PNCT3 a non-literal operand is published by its shape (%r)"
               % (shaped,)) and ok
    got = PNCT.exhaustive_entry("KEY", COND_AGREE, "module", 8)
    ok = check(got["state"] == "ok" and got["value"] == "b"
               and len(got["operands"]) == 2,
               "AC-PNCT3 the entry law resolves the agreeing pair (%r)"
               % (got,)) and ok
    return ok


def ac_pnct4():
    """A match statement is collected as a guarded group and never resolved."""
    rows = loop_rows(MATCH_FIXTURE)
    ok = check(len(rows) == 1 and rows[0]["followed"] == {},
               "AC-PNCT4 a match binding resolves nothing (%r)" % (rows,))
    ok = check(rows and rows[0]["cases"].get("KEY") == 2,
               "AC-PNCT4 the case count is published (%r)"
               % (rows[0]["cases"] if rows else None,)) and ok
    ok = check(rows and rows[0]["refused"].get("KEY")
               == PNCT.REFUSED_MATCH % 2,
               "AC-PNCT4 the match is named with its case count (%r)"
               % (rows[0]["refused"] if rows else None,)) and ok
    groups = rows[0]["exh_groups"] if rows else []
    ok = check(groups and groups[0]["kind"] == PNCT.GROUP_MATCH
               and groups[0]["cases"] == 2
               and [arm for arm in groups[0]["arms"]]
               == ["case0", "case1"],
               "AC-PNCT4 the match is COLLECTED as its own group (%r)"
               % (groups,)) and ok
    base = base_rows(MATCH_FIXTURE)
    ok = check(base and base[0]["refused"].get("KEY") == "unbound",
               "AC-PNCT4 the shipped face did not collect it (%r)"
               % (base[0]["refused"] if base else None,)) and ok
    got = PNCT.exhaustive_entry("KEY", MATCH_FIXTURE, "module", 8)
    ok = check(got["state"] == "refused"
               and got["reason"] == PNCT.REFUSED_MATCH % 2
               and got["cases"] == 2,
               "AC-PNCT4 the entry law never resolves a match (%r)"
               % (got,)) and ok
    return ok


def ac_pnct5():
    """Every shipped answer is carried beside this face own; read-only."""
    base_pairs = ((CHAIN_AGREE, "chain-agree"), (CHAIN_DIFF, "chain-diff"),
                  (TRY_AGREE, "try-agree"), (TRY_DIFF, "try-diff"),
                  (COND_DIFF, "condexpr-diff"), (MATCH_FIXTURE, "match"),
                  (PLAIN, "plain"), (TWO_ARM_AGREE, "two-arm-agree"))
    ok = True
    for text, label in base_pairs:
        base = base_rows(text)[0]
        mine = loop_rows(text)[0]
        ok = check(mine["base_followed"] == base["followed"]
                   and mine["base_refused"] == base["refused"],
                   "AC-PNCT5 the shipped answer is carried unchanged on the "
                   "%s fixture (%r vs %r)"
                   % (label, mine["base_followed"], base["followed"])) and ok
    plain = loop_rows(PLAIN)
    ok = check(plain and plain[0]["followed"].get("KEY") == "b"
               and plain[0]["resolved_by_exhaustive"] == [],
               "AC-PNCT5 an unconditional binding still wins (%r)"
               % (plain,)) and ok
    two_arm = loop_rows(TWO_ARM_AGREE)
    ok = check(two_arm and two_arm[0]["followed"].get("KEY") == "b"
               and two_arm[0]["resolved_by_exhaustive"] == [],
               "AC-PNCT5 an answer the shipped face already gave is not "
               "re-claimed (%r)" % (two_arm,)) and ok
    world = World()
    try:
        world.write("pnct_probe.py", PROBE_FIXTURE)
        before = tree_digest(world.path)
        module_before = digest(MODULE)
        base_before = digest(BASE_MODULE)
        render_before = digest(RENDER_MODULE)
        report = PNCT.audit(world.path, SM)
        ok = check(tree_digest(world.path) == before,
                   "AC-PNCT5 the probed tree is byte-identical after the "
                   "audit") and ok
        ok = check(digest(MODULE) == module_before
                   and digest(BASE_MODULE) == base_before
                   and digest(RENDER_MODULE) == render_before,
                   "AC-PNCT5 the reading moved no shipped digest") and ok
        row = row_of(report, "pnct_probe.py")
        ok = check(row.get("verdict") == PNCT.COVERED,
                   "AC-PNCT5 the probe row still reads COVERED (%r)"
                   % (row.get("verdict"),)) and ok
        ok = check(row.get("exhaustive_loops")
                   and row["exhaustive_loops"][0]["followed"].get("KEY") == "b",
                   "AC-PNCT5 the row carries this face own path loop (%r)"
                   % (row.get("exhaustive_loops"),)) and ok
        ok = check(report["tool"] == PNCT.LABEL
                   and report["verdict"] == PNCT.SEAMS_EXHAUSTIVE_COVERED
                   and report["base_tool"] == PNCG.LABEL,
                   "AC-PNCT5 the report keeps the shipped base label and "
                   "answers its own (%r)"
                   % ((report["tool"], report["verdict"],
                       report.get("base_tool")),)) and ok
        refusal = PNCT.reading(os.path.join(world.path, "absent"), SM)
        ok = check(refusal.get("refusal") == PNCT.E_NO_ROOT
                   and refusal.get("probes") == [],
                   "AC-PNCT5 a missing root is refused, not raised (%r)"
                   % (refusal.get("refusal"),)) and ok
    finally:
        world.close()
    return ok


def ac_pnct6():
    """Pure ASCII, stdlib only, no clock, no network, wired once."""
    text = read_text(MODULE)
    suite = read_text(os.path.abspath(__file__))
    ok = check(all(ord(char) < 128 for char in text),
               "AC-PNCT6 the module source is pure ASCII")
    ok = check(all(ord(char) < 128 for char in suite),
               "AC-PNCT6 this suite source is pure ASCII") and ok
    imports = sorted(set(re.findall(r"(?m)^import ([A-Za-z_][A-Za-z0-9_]*)",
                                    text)))
    allowed = ("argparse", "ast", "hashlib", "json", "os", "sys")
    ok = check(not [name for name in imports if name not in allowed],
               "AC-PNCT6 only the allowed stdlib modules are imported (%s)"
               % (",".join(imports),)) and ok
    forbidden = ("time.time", "datetime", "socket", "urllib", "requests",
                 "http.client", "subprocess")
    ok = check(not [token for token in forbidden if token in text],
               "AC-PNCT6 no clock and no network token in the module") and ok
    registry = read_text(REGISTRY)
    ok = check(WIRED_LABEL in registry and WIRED_SUITE in registry,
               "AC-PNCT6 the face and its suite are wired into the registry "
               "exactly once") and ok
    ok = check(registry.count(WIRED_LABEL) == 1
               and registry.count(WIRED_SUITE) == 1,
               "AC-PNCT6 no duplicate registry row") and ok
    ok = check(PNCT.LABEL
               == "os-probe-seam-name-binding-control-flow-guard-exhaustive",
               "AC-PNCT6 the reconcile label is the face own (%s)"
               % PNCT.LABEL) and ok
    ok = check(PNCT.SEAMS_EXHAUSTIVE_COVERED == "SEAMS-EXHAUSTIVE-COVERED"
               and PNCT.SEAMS_EXHAUSTIVE_STALE == "SEAMS-EXHAUSTIVE-STALE",
               "AC-PNCT6 the reading has its own verdict words (%s/%s)"
               % (PNCT.SEAMS_EXHAUSTIVE_COVERED,
                  PNCT.SEAMS_EXHAUSTIVE_STALE)) and ok
    ok = check(PNCT.REFUSED_CHAIN_ARMS == "exhaustive-arms"
               and PNCT.CHAIN_SEP == ">"
               and PNCT.REFUSED_CONDEXPR == "condexpr:%s|%s"
               and PNCT.REFUSED_MATCH == "match:%d-cases",
               "AC-PNCT6 the new refusal words are its own (%s/%s/%s)"
               % (PNCT.REFUSED_CHAIN_ARMS, PNCT.CHAIN_SEP,
                  PNCT.REFUSED_MATCH)) and ok
    ok = check(PNCG.LABEL
               == "os-probe-seam-name-binding-control-flow-guard-scope",
               "AC-PNCT6 the shipped face it extends is still named") and ok
    return ok


def main():
    print("PROBE SEAM NAME BINDING CONTROL FLOW GUARD EXHAUSTIVE SUITE "
          "(AC-PNCT1..AC-PNCT6)")
    results = [ac_pnct1(), ac_pnct2(), ac_pnct3(), ac_pnct4(), ac_pnct5(),
               ac_pnct6()]
    passed = len([item for item in results if item])
    print("SUITE %s %d/%d criteria green"
          % ("PASS" if passed == EXPECTED_CRITERIA else "FAIL",
             passed, EXPECTED_CRITERIA))
    return 0 if passed == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())