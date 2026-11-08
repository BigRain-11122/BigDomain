"""AC-PNDR1..AC-PNDR6 suite for the alias-chain face (R2555).

Criteria were pinned in state/queue/tech.md:591 at R2553 BEFORE this code
existed.

What this proves: MEASURED at R2553 on the shipped residual-naming face own
reader, a module constant bound to another module constant reads
`name-unbound:B`, a constant declared inside a function body reads
`name-unbound:C`, and a multi-group arm whose leaves disagree publishes both
values under `nested-arms` without naming the group. This face follows a module
alias chain to a FIXPOINT, reads the loop own function body as its own
constant scope, and names the disagreeing group key while still publishing
every leaf by full path.

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

import probe_seam_name_binding_arm_mixed_residual_alias_chain as PNDR  # noqa
import probe_seam_name_binding_arm_mixed_residual_naming as PNDQ  # noqa
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(
    BASE, "probe_seam_name_binding_arm_mixed_residual_alias_chain.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
RESIDUAL_MODULE = os.path.join(
    BASE, "probe_seam_name_binding_arm_mixed_residual_naming.py")
WIRED_LABEL = '"os-probe-seam-name-binding-arm-mixed-residual-alias-chain",'
WIRED_SUITE = ('"test_probe_seam_name_binding_arm_mixed_residual_alias_'
               'chain.py"),')

HELPER = "pndr_helper"

CONTAINER = ('D = {"a": {"b": ("%s",), "z": ("%s",)}}\n'
             % (HELPER, HELPER))

TAIL = 'for name in D["a"][KEY]:\n    pass\n'

TWO_HOP = (CONTAINER
           + 'A = "b"\n'
             'B = A\n'
             'if a1:\n'
             '    KEY = B\n'
             'else:\n'
             '    KEY = B\n'
           + TAIL)

THREE_HOP = (CONTAINER
             + 'A = "b"\n'
               'B = A\n'
               'BB = B\n'
               'if a1:\n'
               '    KEY = BB\n'
               'else:\n'
               '    KEY = BB\n'
             + TAIL)

MIXED_END = (CONTAINER
             + 'AMB = "b"\n'
               'AMB = "z"\n'
               'B = AMB\n'
               'if a1:\n'
               '    KEY = B\n'
               'else:\n'
               '    KEY = B\n'
             + TAIL)

FUNC_CONST = (CONTAINER
              + 'def f():\n'
                '    C = "b"\n'
                '    if a1:\n'
                '        KEY = C\n'
                '    else:\n'
                '        KEY = C\n'
                '    ' + TAIL.replace("\n", "\n    ").rstrip() + '\n')

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

WAS = ('with open("x") as WK:\n'
       '    pass\n'
       + CONTAINER
       + 'if a1:\n'
         '    KEY = "b"\n'
       'else:\n'
       '    KEY = "b"\n'
       + TAIL)

PLAIN = (CONTAINER
         + 'if a1:\n'
           '    KEY = "b"\n'
           'else:\n'
           '    KEY = "b"\n'
         + TAIL)


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


def tail_row(text):
    rows = PNDR.alias_report(text)["loops"]
    return rows[-1] if rows else {}


def entry(text, name):
    row = tail_row(text)
    if not row:
        return {}
    return PNDR.alias_entry(name, text, row["scope"], row["line"])


def shipped(text, name):
    row = tail_row(text)
    if not row:
        return {}
    return PNDQ.residual_entry(name, text, row["scope"], row["line"])


def ac_pndr1():
    """A two-hop module alias chain resolves to the literal it ends in."""
    two = entry(TWO_HOP, "KEY")
    three = entry(THREE_HOP, "KEY")
    base = shipped(TWO_HOP, "KEY")
    ok = check(two.get("state") == PNDR.STATE_OK and two.get("value") == "b",
               "AC-PNDR1 a two-hop chain (B = A, A = 'b') resolves to b")
    ok = check(two.get("alias_chain") == ["B", "A"],
               "AC-PNDR1 the chain it took is published (%s)"
               % (two.get("alias_chain"),)) and ok
    ok = check(three.get("state") == PNDR.STATE_OK
               and three.get("value") == "b"
               and three.get("alias_chain") == ["BB", "B", "A"],
               "AC-PNDR1 a three-name chain follows to a FIXPOINT (%s)"
               % (three.get("alias_chain"),)) and ok
    ok = check(base.get("state") == PNDR.STATE_REFUSED
               and base.get("reason") == "name-unbound:B",
               "AC-PNDR1 the SAME fixture still reads %s on the shipped face"
               % (base.get("reason"),)) and ok
    ok = check(two.get("alias_source") == PNDR.SOURCE_ALIAS
               and two.get("base_residual_reason") == "name-unbound:B",
               "AC-PNDR1 the shipped refusal is carried beside the answer") \
        and ok
    return ok


def ac_pndr2():
    """A chain that ends in two values is NAMEed mixed and publishes nothing."""
    mine = entry(MIXED_END, "KEY")
    base = shipped(MIXED_END, "KEY")
    ok = check(mine.get("state") == PNDR.STATE_REFUSED
               and mine.get("reason") == "name-mixed:AMB",
               "AC-PNDR2 a chain ending in two values reads %s"
               % (mine.get("reason"),))
    ok = check(mine.get("value") is None and not (mine.get("values") or []),
               "AC-PNDR2 no value is published for a mixed chain") and ok
    ok = check(mine.get("mixed_terminal") == "AMB",
               "AC-PNDR2 the LAST name in the chain is named (%s)"
               % (mine.get("mixed_terminal"),)) and ok
    ok = check(base.get("state") == PNDR.STATE_REFUSED
               and base.get("reason") == "name-unbound:B",
               "AC-PNDR2 the SAME fixture reads %s on the shipped face"
               % (base.get("reason"),)) and ok
    return ok


def ac_pndr3():
    """A constant bound in the loop own function body resolves in that scope."""
    mine = entry(FUNC_CONST, "KEY")
    base = shipped(FUNC_CONST, "KEY")
    row = tail_row(FUNC_CONST)
    ok = check(row.get("scope") == "function:f",
               "AC-PNDR3 the fixture loop really sits in a function scope "
               "(%s)" % (row.get("scope"),))
    ok = check(mine.get("state") == PNDR.STATE_OK
               and mine.get("value") == "b",
               "AC-PNDR3 a constant bound in the loop own function body "
               "resolves to b") and ok
    ok = check(mine.get("alias_chain") == ["C"],
               "AC-PNDR3 the function-scope name is the chain it took (%s)"
               % (mine.get("alias_chain"),)) and ok
    ok = check(base.get("state") == PNDR.STATE_REFUSED
               and base.get("reason") == "name-unbound:C",
               "AC-PNDR3 the SAME fixture reads %s on the shipped face"
               % (base.get("reason"),)) and ok
    return ok


def ac_pndr4():
    """A multi-group arm names the group that disagreed, values kept."""
    mine = entry(SEQ_DIFF, "KEY")
    base = shipped(SEQ_DIFF, "KEY")
    ok = check(mine.get("state") == PNDR.STATE_ARMS,
               "AC-PNDR4 a disagreeing multi-group arm stays an arms answer")
    ok = check(mine.get("disagreeing_group") == "if:7"
               and mine.get("reason") == "nested-arms:if:7",
               "AC-PNDR4 the disagreeing group key is NAMED (%s / %s)"
               % (mine.get("disagreeing_group"), mine.get("reason"))) and ok
    ok = check(sorted(mine.get("values") or []) == ["b", "z"],
               "AC-PNDR4 both values are still published (%s)"
               % (mine.get("values"),)) and ok
    leaves = mine.get("leaves") or []
    paths = sorted(leaf["path"] for leaf in leaves)
    values = sorted(leaf["values"][0] for leaf in leaves if leaf["values"])
    ok = check(len(leaves) == 5 and values == ["b", "b", "b", "b", "z"],
               "AC-PNDR4 every leaf is published by FULL path with its value "
               "(%d leaves, %s)" % (len(leaves), values)) and ok
    ok = check("if:2/body>if:7/else" in paths,
               "AC-PNDR4 the disagreeing leaf path is on the row (%s)"
               % (paths,)) and ok
    ok = check(base.get("state") == PNDR.STATE_ARMS
               and base.get("reason") == "nested-arms",
               "AC-PNDR4 the SAME fixture still reads %s on the shipped face"
               % (base.get("reason"),)) and ok
    return ok


def ac_pndr5():
    """Every answer the shipped faces already gave is carried unchanged."""
    fixtures = (("CONST_OK", CONST_OK, ("KEY",)),
                ("WAS", WAS, ("KEY", "WK")),
                ("PLAIN", PLAIN, ("KEY",)))
    failures = []
    for label, text, names in fixtures:
        for name in names:
            mine = entry(text, name)
            base = shipped(text, name)
            same = (mine.get("state") == base.get("state")
                    and mine.get("reason") == base.get("reason")
                    and mine.get("value") == base.get("value"))
            if not same:
                failures.append("%s/%s mine=%s/%s base=%s/%s"
                                % (label, name, mine.get("state"),
                                   mine.get("reason"), base.get("state"),
                                   base.get("reason")))
            if mine.get("base_residual_state") != base.get("state") \
                    or mine.get("base_residual_reason") != base.get("reason"):
                failures.append("%s/%s carried fields disagree" % (label, name))
            if mine.get("alias_source") != PNDR.SOURCE_BASE:
                failures.append("%s/%s source=%s"
                                % (label, name, mine.get("alias_source")))
    ok = check(not failures,
               "AC-PNDR5 every shipped answer is carried unchanged (%s)"
               % (failures[:2] or "no drift",))
    row = tail_row(WAS) or {}
    ok = check(row.get("base_residual_followed") == {"KEY": "b"}
               and row.get("base_residual_refused") == {"WK": "with-as:module"},
               "AC-PNDR5 the residual answers ride on the row itself (%s / %s)"
               % (row.get("base_residual_followed"),
                  row.get("base_residual_refused"))) and ok
    with_as = entry(WAS, "WK")
    ok = check(with_as.get("reason") == "with-as:module"
               and with_as.get("alias_source") == PNDR.SOURCE_BASE,
               "AC-PNDR5 a with-as refusal keeps the shipped reason (%s)"
               % (with_as.get("reason"),)) and ok
    return ok


def ac_pndr6():
    """Pure ASCII, stdlib only, no clock, no network, wired once."""
    text = read_text(MODULE)
    suite = read_text(os.path.abspath(__file__))
    ok = check(all(ord(char) < 128 for char in text),
               "AC-PNDR6 the module source is pure ASCII")
    ok = check(all(ord(char) < 128 for char in suite),
               "AC-PNDR6 this suite source is pure ASCII") and ok
    imports = sorted(set(re.findall(r"(?m)^import ([A-Za-z_][A-Za-z0-9_]*)",
                                    text)))
    allowed = ("argparse", "ast", "hashlib", "json", "os", "sys")
    ok = check(not [name for name in imports if name not in allowed],
               "AC-PNDR6 only the allowed stdlib modules are imported (%s)"
               % (",".join(imports),)) and ok
    forbidden = ("time.time", "datetime", "socket", "urllib", "requests",
                 "http.client", "subprocess")
    ok = check(not [token for token in forbidden if token in text],
               "AC-PNDR6 no clock and no network token in the module") and ok
    registry = read_text(REGISTRY)
    ok = check(WIRED_LABEL in registry and WIRED_SUITE in registry,
               "AC-PNDR6 the face and its suite are wired into the registry") \
        and ok
    ok = check(registry.count(WIRED_LABEL) == 1
               and registry.count(WIRED_SUITE) == 1,
               "AC-PNDR6 no duplicate registry row") and ok
    ok = check(PNDR.LABEL
               == "os-probe-seam-name-binding-arm-mixed-residual-alias-chain",
               "AC-PNDR6 the reconcile label is the face own (%s)"
               % (PNDR.LABEL,)) and ok
    ok = check(PNDR.SEAMS_ALIAS_COVERED == "SEAMS-ALIAS-CHAIN-COVERED"
               and PNDR.SEAMS_ALIAS_STALE == "SEAMS-ALIAS-CHAIN-STALE",
               "AC-PNDR6 the reading has its own verdict words") and ok
    ok = check(os.path.isfile(RESIDUAL_MODULE),
               "AC-PNDR6 the shipped residual face it extends is on disk") \
        and ok
    return ok


def main():
    print("PROBE SEAM NAME BINDING ARM MIXED RESIDUAL ALIAS CHAIN SUITE "
          "(AC-PNDR1..AC-PNDR6)")
    results = [ac_pndr1(), ac_pndr2(), ac_pndr3(), ac_pndr4(), ac_pndr5(),
               ac_pndr6()]
    passed = len([item for item in results if item])
    print("SUITE %s %d/%d criteria green"
          % ("PASS" if passed == EXPECTED_CRITERIA else "FAIL",
             passed, EXPECTED_CRITERIA))
    return 0 if passed == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())