"""AC-DFOB1..AC-DFOB6 suite for the order-field face (R2742).

Criteria were pinned in state/queue/tech.md:703 at R2501 BEFORE this code
existed. Every fixture is built in memory; the scratch dir is removed before
this suite exits and no shipped source file is written. Stdlib only, ASCII
source, zero network, no clock. Exit 0 = all green.
"""

import ast
import os
import shutil
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, BASE)
sys.path.insert(0, SANDBOX)

import export_closeout_gate_parity as PCP  # noqa
import export_parity_difference_order_field as DFOB  # noqa

EXPECTED_CRITERIA = 6
MODULE_NAME = "export_parity_difference_order_field.py"
MODULE = os.path.join(BASE, MODULE_NAME)
SUITE = os.path.join(BASE, "test_" + MODULE_NAME)
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = '"os-export-parity-difference-order-field",'
WIRED_SUITE = '"test_export_parity_difference_order_field.py"'
PREV_LABEL = '"os-closeout-export-parity-wire-binding-consumer",'

SCRATCH = os.path.join(SRC, "..", "tmp", "dfob-R2742-%d" % os.getpid())

ORDER_PAIRS = (
    ('{"x": 1, "y": 2}', '{"y": 2, "x": 1}', "x", "y"),
    ('{"a": 1, "b": 2, "c": 3}', '{"a": 1, "c": 3, "b": 2}', "b", "c"),
    ('{"a": {"x": 1, "y": 2}}', '{"a": {"y": 2, "x": 1}}', "a.x", "a.y"),
    ('{"rows": [{"x": 1, "y": 2}]}', '{"rows": [{"y": 2, "x": 1}]}',
     "rows[0].x", "rows[0].y"),
)

VALUE_PAIRS = (
    ('{"x": 1, "y": 2}', '{"x": 1, "y": 3}', "y"),
    ('{"a": {"y": 2}}', '{"a": {"y": 3}}', "a.y"),
    ('{"x": 1, "y": 2}', '{"x": 1}', "y"),
    ('[1, 2, 3]', '[1, 2, 4]', "list[2]"),
)

UNPARSEABLE = ("not json at all", "{broken: true")


def check(ok, label):
    print("%s %s" % ("PASS" if ok else "FAIL", label))
    return ok


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def write_bytes(path, raw):
    with open(path, "wb") as handle:
        handle.write(raw)


def listdir(path):
    return sorted(os.listdir(path))


def run_cli(env_extra=None):
    """Run the shipped CLI over two scratch files and return (code, out)."""
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    if env_extra:
        env.update(env_extra)
    proc = subprocess.Popen(
        [sys.executable, MODULE, "--left", "left.json",
         "--right", "right.json"],
        cwd=SCRATCH, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    out, err = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace"), \
        err.decode("utf-8", "replace")


def import_names(text):
    """Every module name the source imports, read through the AST."""
    names = []
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.append(node.module)
    return names


def ac_dfob1():
    """AC-DFOB1: the shipped law is asked at CALL time, answer unchanged."""
    ok = check(DFOB.PCP is PCP,
               "AC-DFOB1 the face holds the SHIPPED module object, not a copy")
    original = PCP.first_difference
    try:
        PCP.first_difference = lambda left, right: "PATCHED-FIELD"
        patched = DFOB.report_of('{"x": 1}', '{"x": 2}')
    finally:
        PCP.first_difference = original
    ok = check(patched["differs"] == "PATCHED-FIELD",
               "AC-DFOB1 a patched shipped law moves differs (%r)"
               % (patched["differs"],)) and ok
    same = True
    for left, right, _order, _other in ORDER_PAIRS:
        report = DFOB.report_of(left, right)
        expected = PCP.first_difference(left, right)
        if report["differs"] != expected or expected != "bytes":
            same = False
            print("  detail left=%r differs=%r expected=%r"
                  % (left, report["differs"], expected))
    ok = check(same,
               "AC-DFOB1 the published answer equals first_difference on "
               "every order pair, byte for byte") and ok
    ok = check(DFOB.report_of('{"x": 1}', '{"x": 2}')["differs"] == "x",
               "AC-DFOB1 the restored law answers the real field (x)") and ok
    return ok


def ac_dfob2():
    """AC-DFOB2: order-only is named by the first key that moved, both ways."""
    ok = True
    for left, right, forward, backward in ORDER_PAIRS:
        blind = PCP.first_difference(left, right)
        report = DFOB.report_of(left, right)
        ok = check(blind == "bytes" and report["differs"] == "bytes",
                   "AC-DFOB2 shipped law reads the shape word on %r (%r)"
                   % (left, blind)) and ok
        ok = check(report["order_field"] == forward
                   and report["order_only"] is True
                   and report["verdict"] == "ORDER-ONLY",
                   "AC-DFOB2 forward order names the first moved key %r (%r)"
                   % (forward, report["order_field"])) and ok
        back = DFOB.report_of(right, left)
        ok = check(back["order_field"] == backward
                   and back["order_only"] is True
                   and back["verdict"] == "ORDER-ONLY",
                   "AC-DFOB2 the OTHER order names its own first key %r (%r)"
                   % (backward, back["order_field"])) and ok
        ok = check(back["order_field"] != forward,
                   "AC-DFOB2 the two orders do not fake one answer") and ok
    return ok


def ac_dfob3():
    """AC-DFOB3: a value difference keeps exactly the shipped field."""
    ok = True
    for left, right, expected in VALUE_PAIRS:
        shipped = PCP.first_difference(left, right)
        report = DFOB.report_of(left, right)
        ok = check(shipped == expected and report["differs"] == expected,
                   "AC-DFOB3 differs stays the shipped field %r (%r)"
                   % (expected, report["differs"])) and ok
        ok = check(report["order_field"] == ""
                   and report["order_only"] is False,
                   "AC-DFOB3 no order claim rides on a value difference (%r)"
                   % (report["order_field"],)) and ok
        ok = check(report["verdict"] == "VALUE",
                   "AC-DFOB3 the verdict reads VALUE (%r)"
                   % (report["verdict"],)) and ok
    reordered = '{"y": 9, "x": 1}'
    mixed = DFOB.report_of('{"x": 1, "y": 2}', reordered)
    ok = check(mixed["differs"] == "y" and mixed["order_field"] == "",
               "AC-DFOB3 reorder PLUS a value difference names the value "
               "field and claims no order (%r/%r)"
               % (mixed["differs"], mixed["order_field"])) and ok
    return ok


def ac_dfob4():
    """AC-DFOB4: identical reads nothing; unparseable keeps the shape word."""
    ok = True
    for text in ('{"x": 1, "y": 2}', "not json at all", ""):
        report = DFOB.report_of(text, text)
        ok = check(report["differs"] == "" and report["order_field"] == ""
                   and report["order_only"] is False
                   and report["verdict"] == "IDENTICAL",
                   "AC-DFOB4 byte-identical text reads no difference (%r)"
                   % (text,)) and ok
    left, right = UNPARSEABLE
    shipped = PCP.first_difference(left, right)
    report = DFOB.report_of(left, right)
    ok = check(shipped == "bytes" and report["differs"] == "bytes",
               "AC-DFOB4 an unparseable pair keeps the shipped shape word "
               "(%r)" % (report["differs"],)) and ok
    ok = check(report["order_field"] == ""
               and report["verdict"] == "UNPARSEABLE",
               "AC-DFOB4 an unparseable pair is never given an order field "
               "(%r/%r)" % (report["order_field"], report["verdict"])) and ok
    spaced = DFOB.report_of('{ "x": 1 }', '{"x":1}')
    ok = check(spaced["differs"] == "bytes" and spaced["order_field"] == ""
               and spaced["verdict"] == "FORMAT",
               "AC-DFOB4 a whitespace-only difference is named FORMAT and "
               "claims no moved key (%r/%r)"
               % (spaced["verdict"], spaced["order_field"])) and ok
    return ok


def receiver_name(node):
    """The base name of an attribute chain, e.g. sys.stdout.write -> sys."""
    while isinstance(node, ast.Attribute):
        node = node.value
    return node.id if isinstance(node, ast.Name) else ""


def disk_mutations(tree):
    """Every call that could mutate the tree, with console writes allowed.

    sys.stdout / sys.stderr are the console, not the tree, and str.replace is
    not os.replace - both were false positives of the first version of this
    scanner, which is why the rule is stated per receiver and not per name.
    """
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute):
            continue
        attr = func.attr
        base = receiver_name(func)
        if attr in ("write", "writelines"):
            if base != "sys":
                found.append("%s.%s" % (base or "?", attr))
        elif attr == "replace":
            if base in ("os", "shutil"):
                found.append("%s.%s" % (base, attr))
        elif attr in ("remove", "unlink", "rmtree", "rename", "mkdir",
                      "makedirs"):
            found.append("%s.%s" % (base or "?", attr))
    return found


def ac_dfob5():
    """AC-DFOB5: read-only - writes nothing, reads no clock."""
    tree = ast.parse(read_bytes(MODULE).decode("ascii"))
    bad_open = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "open":
                mode = None
                if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                    mode = node.args[1].value
                if mode != "rb":
                    bad_open.append(mode)
    bad_calls = disk_mutations(tree)
    ok = check(not bad_open,
               "AC-DFOB5 every open() call in the face is read-binary (%r)"
               % (bad_open,))
    ok = check(not bad_calls,
               "AC-DFOB5 no write/remove/rename call exists (%r)"
               % (bad_calls,)) and ok
    clock = [name for name in import_names(read_bytes(MODULE).decode("ascii"))
             if name.split(".")[0] in ("time", "datetime", "socket", "http",
                                       "urllib", "requests")]
    ok = check(not clock,
               "AC-DFOB5 the face imports no clock and no network (%r)"
               % (clock,)) and ok
    before = listdir(SCRATCH)
    before_left = read_bytes(os.path.join(SCRATCH, "left.json"))
    before_right = read_bytes(os.path.join(SCRATCH, "right.json"))
    code, out, err = run_cli()
    ok = check(code == 0 and "order_field=x" in out and "differs=bytes" in out,
               "AC-DFOB5 the CLI compares and names the moved key (rc=%d, "
               "%r)" % (code, out.strip())) and ok
    after = listdir(SCRATCH)
    ok = check(before == after,
               "AC-DFOB5 the CLI created no file in the tree it read (%r)"
               % (after,)) and ok
    ok = check(read_bytes(os.path.join(SCRATCH, "left.json")) == before_left
               and read_bytes(os.path.join(SCRATCH, "right.json")) == before_right,
               "AC-DFOB5 both sources are byte-identical after the run") and ok
    missing = subprocess.Popen(
        [sys.executable, MODULE, "--left", "absent.json",
         "--right", "right.json"],
        cwd=SCRATCH, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out2, err2 = missing.communicate()
    text2 = out2.decode("utf-8", "replace") + err2.decode("utf-8", "replace")
    ok = check(missing.returncode == 2 and DFOB.E_NO_SOURCE in text2,
               "AC-DFOB5 a missing source refuses at its own exit code (%d, "
               "%r)" % (missing.returncode, text2.strip())) and ok
    return ok


def ac_dfob6():
    """AC-DFOB6: ASCII, stdlib only, own label and own suite."""
    raw = read_bytes(MODULE)
    ok = check(not any(byte >= 128 for byte in raw),
               "AC-DFOB6 the module source is pure ASCII (%d bytes)"
               % (len(raw),))
    text = raw.decode("ascii")
    banned = [name for name in ("import time", "import datetime",
                                "import socket", "import urllib",
                                "import http", "shell=True")
              if name in text]
    ok = check(not banned, "AC-DFOB6 no clock, no network, no shell (%s)"
               % (banned,)) and ok
    allowed = ("argparse", "json", "sys", "export_closeout_gate_parity")
    bad = [name for name in import_names(text)
           if name.split(".")[0] not in allowed]
    ok = check(not bad and import_names(text),
               "AC-DFOB6 every import is stdlib or the shipped law (%r)"
               % (bad,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8")
    ok = check(registry.count(WIRED_LABEL) == 1,
               "AC-DFOB6 the registry carries exactly one label row (%d)"
               % (registry.count(WIRED_LABEL),)) and ok
    ok = check(registry.count(WIRED_SUITE) == 1,
               "AC-DFOB6 the registry carries exactly one suite row (%d)"
               % (registry.count(WIRED_SUITE),)) and ok
    ok = check(registry.count(PREV_LABEL) == 1,
               "AC-DFOB6 the shipped parity-wire row is untouched (%d)"
               % (registry.count(PREV_LABEL),)) and ok
    ok = check(os.path.isfile(SUITE),
               "AC-DFOB6 this suite exists on disk") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-DFOB6 six criteria are declared") and ok
    ok = check(DFOB.LABEL == "os-export-parity-difference-order-field",
               "AC-DFOB6 the face carries its own reconcile label (%r)"
               % (DFOB.LABEL,)) and ok
    return ok


def main():
    if not os.path.isdir(SCRATCH):
        os.makedirs(SCRATCH)
    write_bytes(os.path.join(SCRATCH, "left.json"),
                b'{"x": 1, "y": 2}\n')
    write_bytes(os.path.join(SCRATCH, "right.json"),
                b'{"y": 2, "x": 1}\n')
    checks = [ac_dfob1, ac_dfob2, ac_dfob3, ac_dfob4, ac_dfob5, ac_dfob6]
    try:
        results = [func() for func in checks]
    finally:
        shutil.rmtree(SCRATCH, ignore_errors=True)
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 2


if __name__ == "__main__":
    sys.exit(main())
