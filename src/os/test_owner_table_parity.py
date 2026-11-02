"""owner_table_parity suite (R2390; criteria pinned inside the R2383 tech seed
row of state/queue/tech.md:445 BEFORE this code existed).

The seeded labels were AC-OTP1..AC-OTP6 / E_OTP; those are already owned by
src/os/orphan_promote.py at HEAD, so this suite pins the free labels
AC-OTPP1..AC-OTPP6 for the SAME six substantive criteria (disclosed in the
module docstring and on the board row, not swept).

What this proves: a tool's own help table and its parser are two hand-written
descriptions of one flag set, and nothing compared them.

  AC-OTPP1 the reader takes the table AND the parser source from the tool it
           is pointed at, and names each flag on the side it is missing from -
           a literal comparison, a membership tuple and a startswith prefix
           all count as parser-accepted, each fixture leg proving one;
  AC-OTPP2 a tool whose table and parser agree reads PARITY-AGREES at exit 0
           while a one-sided tool reads PARITY-DISAGREES naming the flag and
           its side, and editing the TABLE of the same file flips the verdict,
           so the reading is a property of the code and not a whitelist;
  AC-OTPP3 the reader writes nothing and reads no clock: the audited file's
           bytes and mtime are unchanged, and the module carries no write
           primitive and no clock import;
  AC-OTPP4 a tool with no own-flag table reads NO-TABLE at exit 2 rather than
           PARITY-AGREES by accident;
  AC-OTPP5 exit 0 = AGREES, 2 = DISAGREES or NO-TABLE, 3 = missing path,
           5 = bad flags, with a byte-stable --json over the pinned keys;
  AC-OTPP6 pure ASCII, stdlib only, zero network, plus its own reconcile label
           wired into the runner.

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
sys.path.insert(0, BASE)

import owner_table_parity as OTP  # noqa: E402

MODULE = os.path.join(BASE, "owner_table_parity.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-owner-table-parity"
WIRED_EXPECT = '"test_owner_table_parity.py"), 6),'

DISAGREE = (
    'FLAGS = ("--alpha", "--beta")\n'
    '\n'
    'def main(argv):\n'
    '    exact = []\n'
    '    for token in argv:\n'
    '        if token == "--alpha":\n'
    '            exact.append(token)\n'
    '        elif token in ("--gamma",):\n'
    '            exact.append(token)\n'
    '        elif token.startswith("--delta"):\n'
    '            exact.append(token)\n'
    '    return exact\n'
)

AGREE = (
    'FLAGS = ("--one", "--two")\n'
    '\n'
    'def main(argv):\n'
    '    for token in argv:\n'
    '        if token == "--one":\n'
    '            pass\n'
    '        if token == "--two":\n'
    '            pass\n'
    '    return 0\n'
)

NO_TABLE = (
    'def main(argv):\n'
    '    for token in argv:\n'
    '        if token == "--solo":\n'
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
    world = tempfile.mkdtemp(prefix="otp-world-")
    return world


def write_tool(world, name, body):
    path = os.path.join(world, name)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    return path


def run_cli(world, args):
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.Popen([sys.executable, MODULE] + args, cwd=world,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=env)
    out, err = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace"), \
        err.decode("utf-8", "replace")


def reading(world, body, name="tool.py"):
    path = write_tool(world, name, body)
    payload = OTP.audit(path)
    return payload


def ac_otpp1():
    """Every accepted-token shape is read, and both sides of the gap named."""
    world = make_world()
    payload = reading(world, DISAGREE)
    exact_leg = "--gamma" in payload["parser"]
    member_leg = "--gamma" in payload["parser"]
    prefix_leg = "--delta" in payload["prefix"]
    table_leg = payload["table"] == ["--alpha", "--beta"]
    named = (payload["missing_in_table"] == ["--delta*", "--gamma"]
             and payload["missing_in_parser"] == ["--beta"])
    shutil.rmtree(world, ignore_errors=True)
    ok = exact_leg and member_leg and prefix_leg and table_leg and named
    if not ok:
        print("  measured: %r" % (payload,), flush=True)
    check(ok, "AC-OTPP1 the table and the parser source are both read from the "
              "pointed tool - literal, membership and startswith legs - and "
              "each flag is named on the side it is missing from")


def ac_otpp2():
    """Agreeing reads AGREES; one-sided reads DISAGREES; the table moves it."""
    world = make_world()
    agree_rc, agree_out, _ = run_cli(world, [write_tool(world, "agree.py",
                                                       AGREE)])
    disagree_path = write_tool(world, "disagree.py", DISAGREE)
    dis_rc, dis_out, _ = run_cli(world, [disagree_path])
    # the SAME parser with one table entry removed must still refuse: the
    # verdict follows the tool's code, not a name on a list.
    patched = write_tool(world, "agree.py",
                         AGREE.replace('("--one", "--two")', '("--one",)'))
    pat_rc, pat_out, _ = run_cli(world, [patched])
    shutil.rmtree(world, ignore_errors=True)
    ok = (agree_rc == 0 and "verdict=PARITY-AGREES" in agree_out
          and dis_rc == 2 and "verdict=PARITY-DISAGREES" in dis_out
          and "missing_in_table=[--delta*,--gamma]" in dis_out
          and "missing_in_parser=[--beta]" in dis_out
          and pat_rc == 2 and "verdict=PARITY-DISAGREES" in pat_out
          and "missing_in_table=[--two]" in pat_out)
    if not ok:
        print("  measured: agree=(%r,%r) disagree=(%r,%r) patched=(%r,%r)"
              % (agree_rc, agree_out.strip(), dis_rc, dis_out.strip(),
                 pat_rc, pat_out.strip()), flush=True)
    check(ok, "AC-OTPP2 an agreeing tool reads PARITY-AGREES at exit 0, a "
              "one-sided tool names the flag and its side at exit 2, and "
              "removing one table entry from the SAME parser flips it")


def ac_otpp3():
    """Nothing is written and no clock is read."""
    world = make_world()
    path = write_tool(world, "tool.py", AGREE)
    with io.open(path, "rb") as handle:
        before = handle.read()
    before_mtime = os.stat(path).st_mtime
    run_cli(world, [path])
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
    shutil.rmtree(world, ignore_errors=True)
    ok = unchanged and no_write and no_clock
    if not ok:
        print("  measured: unchanged=%r no_write=%r no_clock=%r imports=%r"
              % (unchanged, no_write, no_clock, sorted(imported)), flush=True)
    check(ok, "AC-OTPP3 the audited file's bytes and mtime are unchanged and "
              "the module carries no write primitive and no clock import")


def ac_otpp4():
    """No own-flag table reads NO-TABLE, never AGREES."""
    world = make_world()
    path = write_tool(world, "solo.py", NO_TABLE)
    rc, out, _ = run_cli(world, [path])
    shutil.rmtree(world, ignore_errors=True)
    ok = (rc == 2 and "verdict=NO-TABLE" in out
          and "E_OTPP_NO_TABLE" in out
          and "PARITY-AGREES" not in out)
    if not ok:
        print("  measured: (%r,%r)" % (rc, out.strip()), flush=True)
    check(ok, "AC-OTPP4 a tool with no own-flag table reads NO-TABLE at exit "
              "2 rather than PARITY-AGREES by accident")


def ac_otpp5():
    """Exit codes 0/2/3/5 and a byte-stable --json over the pinned keys."""
    world = make_world()
    agree = write_tool(world, "agree.py", AGREE)
    rc_ok, _, _ = run_cli(world, [agree])
    rc_dis, _, _ = run_cli(world, [write_tool(world, "disagree.py",
                                              DISAGREE)])
    rc_missing, _, _ = run_cli(world, ["does-not-exist.py"])
    rc_bad, _, _ = run_cli(world, ["--nope", agree])
    first = run_cli(world, [agree, "--json"])[1]
    second = run_cli(world, [agree, "--json"])[1]
    stable = first == second and first.strip() != ""
    keys = []
    if stable:
        keys = list(json.loads(first).keys())
    payload_keys = list(OTP.JSON_KEYS)
    shutil.rmtree(world, ignore_errors=True)
    ok = (rc_ok == 0 and rc_dis == 2 and rc_missing == 3 and rc_bad == 5
          and stable and keys == sorted(payload_keys))
    if not ok:
        print("  measured: codes=(%r,%r,%r,%r) stable=%r keys=%r"
              % (rc_ok, rc_dis, rc_missing, rc_bad, stable, keys), flush=True)
    check(ok, "AC-OTPP5 exits are 0/2/3/5 and --json is byte-stable over the "
              "pinned key set")


def ac_otpp6():
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
    ok = (all(byte < 128 for byte in raw)
          and imported <= {"ast", "io", "json", "os", "sys"}
          and "socket" not in body and "urllib" not in body
          and "requests" not in body
          and WIRED_EXPECT in runner
          and ('"%s"' % LABEL) in runner)
    if not ok:
        print("  measured: ascii=%r imports=%r wired=%r label=%r"
              % (all(byte < 128 for byte in raw), sorted(imported),
                 WIRED_EXPECT in runner, ('"%s"' % LABEL) in runner),
              flush=True)
    check(ok, "AC-OTPP6 the module is pure ASCII stdlib with no network and "
              "its own reconcile label is wired into the runner")


def main():
    ac_otpp1()
    ac_otpp2()
    ac_otpp3()
    ac_otpp4()
    ac_otpp5()
    ac_otpp6()
    print("SUMMARY passes=%d fails=%d" % (PASSES, FAILS), flush=True)
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())