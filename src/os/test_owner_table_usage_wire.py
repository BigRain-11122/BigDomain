"""owner_table_usage_wire suite (R2399; criteria AC-OTUW1..AC-OTUW6 pinned
inside the R2390 tech seed row of state/queue/tech.md:460 BEFORE this code).

What this proves: owner_table_parity reads every module-level UPPER_CASE
constant carrying flag-shaped literals as a declared own-flag table, so a tool
whose DATA happens to look like flags reads as a one-sided table and the
reading cries wolf. A constant is a table only when a help or usage path in
the same file reads it.

  AC-OTUW1 a constant named by the module's own usage/help path counts as a
           table while a constant no usage path names does not, proved by
           patching the path (usage_paths returning nothing) and watching the
           reading move from PARITY-AGREES to NO-TABLE and back;
  AC-OTUW2 the three MEASURED data-constant false positives
           (evidence_R2372.py, r2140_fold.py, retry_naming.py) read NO-TABLE
           after the change while runner_arg_guard.py keeps PARITY-DISAGREES
           naming its own two tokens and battery_followup.py keeps
           PARITY-AGREES 8/8 - false positives removed, no true one lost;
  AC-OTUW3 the reading is derived from source (no whitelist file, no
           hard-coded tool name) so a NEW tool with a one-sided usage table
           reads DISAGREES with no edit;
  AC-OTUW4 the module writes nothing and reads no clock, and the shipped
           owner_table_parity is untouched (its on-disk bytes equal git HEAD's)
           with its refusal codes, exit codes and printed lines reproduced
           identically before and after this module runs;
  AC-OTUW5 exits are 0/2/3/5 with a byte-stable --json over the shipped key
           set;
  AC-OTUW6 pure ASCII, stdlib only, zero network, own reconcile label wired
           into the runner.

Stdlib only, one throwaway world per case, no network.
"""

import ast
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import owner_table_parity as OTP  # noqa: E402
import owner_table_usage_wire as OUTW  # noqa: E402

MODULE = os.path.join(BASE, "owner_table_usage_wire.py")
LAW_MODULE = os.path.join(BASE, "owner_table_parity.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-owner-table-usage-wire"
WIRED_EXPECT = '"test_owner_table_usage_wire.py"), 6),'

USAGE_TABLE = (
    'FLAGS = ("--alpha", "--beta")\n'
    'DATA = ["--round", "R2399", "--until", "R2400"]\n'
    '\n'
    'def usage():\n'
    '    print(FLAGS)\n'
    '\n'
    'def main(argv):\n'
    '    for token in argv:\n'
    '        if token == "--alpha":\n'
    '            pass\n'
    '        if token == "--beta":\n'
    '            pass\n'
    '    return 0\n'
)

NEW_ONE_SIDED = (
    'FLAGS = ("--one",)\n'
    '\n'
    'def usage():\n'
    '    print("usage: tool.py --one")\n'
    '    print(FLAGS)\n'
    '\n'
    'def main(argv):\n'
    '    for token in argv:\n'
    '        if token == "--one":\n'
    '            pass\n'
    '        elif token == "--two":\n'
    '            pass\n'
    '    return 0\n'
)

PASSES = 0
FAILS = 0


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


def make_world():
    return tempfile.mkdtemp(prefix="otuw-world-")


def write_tool(world, name, body):
    path = os.path.join(world, name)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    return path


def run_cli(module_path, cwd, args):
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.Popen([sys.executable, module_path] + args, cwd=cwd,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=env)
    out, err = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace"), \
        err.decode("utf-8", "replace")


def reading(world, body, name="tool.py"):
    return OUTW.audit(write_tool(world, name, body))


def ac_otuw1():
    """A usage-named constant is a table; a data constant is not; patch moves it."""
    world = make_world()
    path = write_tool(world, "tool.py", USAGE_TABLE)
    payload = OUTW.audit(path)
    named = payload["table"] == ["--alpha", "--beta"]
    data_out = "--round" not in payload["table"]
    agrees = payload["verdict"] == OTP.VERDICT_AGREES and payload["parser"] == \
        ["--alpha", "--beta"]
    original = OUTW.usage_paths
    try:
        OUTW.usage_paths = lambda tree: []
        blanked = OUTW.audit(path)
    finally:
        OUTW.usage_paths = original
    restored = OUTW.audit(path)
    shutil.rmtree(world, ignore_errors=True)
    moved = (blanked["verdict"] == OTP.VERDICT_NO_TABLE
             and blanked["table"] == []
             and restored["verdict"] == OTP.VERDICT_AGREES
             and restored["table"] == ["--alpha", "--beta"])
    ok = named and data_out and agrees and moved
    if not ok:
        print("  measured: named=%r data_out=%r agrees=%r blanked=%r "
              "restored=%r" % (named, data_out, agrees, blanked["verdict"],
                               restored["verdict"]), flush=True)
    check(ok, "AC-OTUW1 the usage path decides which constants are a table, "
              "and patching that path moves the reading")


def ac_otuw2():
    """The three measured false positives stop, the two true readings stay."""
    measured = [
        ("evidence_R2372.py", OTP.VERDICT_NO_TABLE, [], []),
        ("r2140_fold.py", OTP.VERDICT_NO_TABLE, [], []),
        ("retry_naming.py", OTP.VERDICT_NO_TABLE, [], []),
        ("runner_arg_guard.py", OTP.VERDICT_DISAGREES,
         ["--guard*", "--help"], []),
        ("battery_followup.py", OTP.VERDICT_AGREES, [], []),
    ]
    bad = []
    detail = []
    for name, verdict, missing_table, missing_parser in measured:
        path = os.path.join(BASE, name)
        payload = OUTW.audit(path)
        detail.append("%s=%s" % (name, payload["verdict"]))
        if payload["verdict"] != verdict:
            bad.append(name + ":verdict")
        if missing_table and payload["missing_in_table"] != missing_table:
            bad.append(name + ":missing_in_table")
        if missing_parser and payload["missing_in_parser"] != missing_parser:
            bad.append(name + ":missing_in_parser")
    followup = OUTW.audit(os.path.join(BASE, "battery_followup.py"))
    sizes = len(followup["table"]) == 8 and len(followup["parser"]) == 8
    ok = not bad and sizes
    if not ok:
        print("  measured: %s bad=%r sizes=%r"
              % (" ".join(detail), bad, sizes), flush=True)
    check(ok, "AC-OTUW2 the three data-constant false positives read NO-TABLE "
              "while runner_arg_guard keeps its real drift and "
              "battery_followup keeps AGREES 8/8")


def ac_otuw3():
    """Derived from source: a brand-new one-sided tool refuses with no edit."""
    world = make_world()
    path = write_tool(world, "brand_new.py", NEW_ONE_SIDED)
    payload = OUTW.audit(path)
    rc, out, _ = run_cli(MODULE, world, [path])
    with io.open(MODULE, encoding="utf-8") as handle:
        text = handle.read()
    tree = ast.parse(text)
    # AC-OTUW3 intent: no tool name is a DECISION. The module docstring cites
    # the five measured files as evidence (that is prose and must stay
    # truthful), so the check reads every string constant that is NOT a
    # docstring - a name reaching the reading through data would show there.
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef,
                             ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and \
                    isinstance(body[0].value, ast.Constant) and \
                    isinstance(body[0].value.value, str):
                docstrings.add(id(body[0].value))
    names = ("runner_arg_guard", "battery_followup", "evidence_R2372",
             "r2140_fold", "retry_naming")
    data_strings = [node.value for node in ast.walk(tree)
                    if isinstance(node, ast.Constant)
                    and isinstance(node.value, str)
                    and id(node) not in docstrings]
    no_names = not any(name in value for name in names
                       for value in data_strings)
    no_whitelist = "WHITELIST" not in text and "whitelist file" not in text
    ok = (payload["verdict"] == OTP.VERDICT_DISAGREES
          and payload["missing_in_table"] == ["--two"]
          and payload["missing_in_parser"] == []
          and rc == 2 and "missing_in_table=[--two]" in out
          and no_names and no_whitelist)
    shutil.rmtree(world, ignore_errors=True)
    if not ok:
        print("  measured: %r rc=%r no_names=%r no_whitelist=%r"
              % (payload, rc, no_names, no_whitelist), flush=True)
    check(ok, "AC-OTUW3 a NEW one-sided tool reads DISAGREES with no edit, and "
              "the reading carries no tool name and no whitelist")


def ac_otuw4():
    """No write, no clock; the shipped law's own face is untouched."""
    world = make_world()
    path = write_tool(world, "tool.py", USAGE_TABLE)
    with io.open(path, "rb") as handle:
        before = handle.read()
    before_mtime = os.stat(path).st_mtime
    run_cli(MODULE, world, [path])
    with io.open(path, "rb") as handle:
        after = handle.read()
    after_mtime = os.stat(path).st_mtime
    with io.open(MODULE, encoding="utf-8") as handle:
        text = handle.read()
    tree = ast.parse(text)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    body = "\n".join(line for line in text.splitlines()
                     if not line.lstrip().startswith("#"))
    no_write = (".write(" not in body and "os.replace" not in body
                and "os.remove" not in body and "tempfile" not in body
                and "mkstemp" not in body and "shutil" not in body
                and '"w"' not in body and '"a"' not in body)
    no_clock = ("time" not in imported and "datetime" not in imported
                and "os.utime" not in body)
    unchanged = before == after and before_mtime == after_mtime
    # the shipped law must be byte-identical to git HEAD: this window adds a
    # notion, it does not edit the face it borrows.
    head = subprocess.Popen(
        ["git", "show", "HEAD:src/os/owner_table_parity.py"], cwd=REPO,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    head_out, _ = head.communicate()
    with io.open(LAW_MODULE, "rb") as handle:
        law_disk = handle.read()
    law_same = head.returncode == 0 and head_out == law_disk
    # and its printed lines still reproduce identically around this module
    guard = os.path.join(BASE, "runner_arg_guard.py")
    before_call = run_cli(LAW_MODULE, BASE, [guard])
    OUTW.audit(guard)
    after_call = run_cli(LAW_MODULE, BASE, [guard])
    law_face = before_call == after_call and before_call[0] == 2
    shutil.rmtree(world, ignore_errors=True)
    ok = (unchanged and no_write and no_clock and law_same and law_face)
    if not ok:
        print("  measured: unchanged=%r no_write=%r no_clock=%r law_same=%r "
              "law_face=%r imports=%r"
              % (unchanged, no_write, no_clock, law_same, law_face,
                 sorted(imported)), flush=True)
    check(ok, "AC-OTUW4 nothing is written, no clock is read, and "
              "owner_table_parity's bytes and printed lines are unchanged")


def ac_otuw5():
    """Exits 0/2/3/5 and a byte-stable --json over the shipped keys."""
    world = make_world()
    agree = write_tool(world, "agree.py", USAGE_TABLE)
    rc_ok, out_ok, _ = run_cli(MODULE, world, [agree])
    rc_dis, _, _ = run_cli(MODULE, world, [write_tool(world, "side.py",
                                                     NEW_ONE_SIDED)])
    rc_missing, _, _ = run_cli(MODULE, world, ["does-not-exist.py"])
    rc_bad, _, _ = run_cli(MODULE, world, ["--nope", agree])
    first = run_cli(MODULE, world, [agree, "--json"])[1]
    second = run_cli(MODULE, world, [agree, "--json"])[1]
    stable = first == second and first.strip() != ""
    keys = list(json.loads(first).keys()) if stable else []
    shutil.rmtree(world, ignore_errors=True)
    ok = (rc_ok == 0 and "verdict=PARITY-AGREES" in out_ok
          and rc_dis == 2 and rc_missing == 3 and rc_bad == 5
          and stable and keys == sorted(list(OTP.JSON_KEYS)))
    if not ok:
        print("  measured: codes=(%r,%r,%r,%r) stable=%r keys=%r"
              % (rc_ok, rc_dis, rc_missing, rc_bad, stable, keys), flush=True)
    check(ok, "AC-OTUW5 exits are 0/2/3/5 and --json is byte-stable over the "
              "shipped key set")


def ac_otuw6():
    """Pure ASCII stdlib, no network, own reconcile label wired."""
    with io.open(MODULE, "rb") as handle:
        raw = handle.read()
    text = raw.decode("utf-8")
    tree = ast.parse(text)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    body = "\n".join(line for line in text.splitlines()
                     if not line.lstrip().startswith("#"))
    with io.open(RUNNER, encoding="utf-8") as handle:
        runner = handle.read()
    # "stdlib only" here means no third-party and no network dependency. The
    # one non-stdlib name is owner_table_parity - the shipped law this reader
    # asks at call time, which AC-OTUW4 requires and which lives in this tree.
    ok = (all(byte < 128 for byte in raw)
          and imported <= {"ast", "io", "json", "os", "sys",
                           "owner_table_parity"}
          and "socket" not in body and "urllib" not in body
          and "requests" not in body
          and WIRED_EXPECT in runner
          and ('"%s"' % LABEL) in runner)
    if not ok:
        print("  measured: ascii=%r imports=%r wired=%r label=%r"
              % (all(byte < 128 for byte in raw), sorted(imported),
                 WIRED_EXPECT in runner, ('"%s"' % LABEL) in runner),
              flush=True)
    check(ok, "AC-OTUW6 the module is pure ASCII stdlib with no network and "
              "its own reconcile label is wired into the runner")


def main():
    ac_otuw1()
    ac_otuw2()
    ac_otuw3()
    ac_otuw4()
    ac_otuw5()
    ac_otuw6()
    print("SUMMARY passes=%d fails=%d" % (PASSES, FAILS), flush=True)
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())