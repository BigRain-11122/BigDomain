"""owner_table_reader_parity suite (R2412; criteria AC-OTRP1..AC-OTRP6 pinned
inside the R2399 tech seed row of state/queue/tech.md:480 BEFORE this code).

What this proves: owner_table_parity answers "does the declared table match
the parser" and owner_table_usage_wire answers "which constants are the
declared table". Both are right about their own question and they disagree on
the same tree, so an operator holding either log alone cannot tell a tool with
NO table from a tool whose usage path is named neither way.

  AC-OTRP1 both readings are asked of the two shipped modules at CALL time, so
           patching either one moves the disagreement list;
  AC-OTRP2 every row names both verdicts and, for a law-only table, the flags
           the law reported, never a canned number;
  AC-OTRP3 a tree where both readers agree over every file reads PARITY-CLEAN
           at exit 0 while any disagreement reads PARITY-SPLIT at exit 2;
  AC-OTRP4 the historical one-per-round copies are classified as superseded by
           the single callable rather than counted as debt, and that
           classification is derived from the filename family, not a whitelist
           file (delete the base and the row returns to debt);
  AC-OTRP5 CLI exits 0/2/3/5 with a byte-stable --json over pinned keys;
  AC-OTRP6 pure ASCII, stdlib only, no clock, no network, read-only, plus its
           own reconcile label wired into the runner.

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
import owner_table_reader_parity as OTRP  # noqa: E402

MODULE = os.path.join(BASE, "owner_table_reader_parity.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-owner-table-reader-parity"
WIRED_EXPECT = '"test_owner_table_reader_parity.py"), 6),'

# both readers agree: the table is named by a usage path and the parser
# accepts exactly it.
AGREES_TOOL = (
    'FLAGS = ("--alpha", "--beta")\n'
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

# no table at all on either side.
BARE_TOOL = (
    'def main(argv):\n'
    '    return 0\n'
)

# the law reads a table, the usage wire correctly reads none: the row shape
# the wire was built to remove and this face publishes.
LAW_ONLY_TOOL = (
    'ARGS = ["--round", "R2001", "--until", "R2002", "--json"]\n'
    '\n'
    'def main(argv):\n'
    '    return 0\n'
)

# both readers see a table and the tables differ.
TABLES_DIFFER_TOOL = (
    'FLAGS = ("--alpha",)\n'
    'DATA = ("--zzz",)\n'
    '\n'
    'def usage():\n'
    '    print(FLAGS)\n'
    '\n'
    'def main(argv):\n'
    '    for token in argv:\n'
    '        if token == "--alpha":\n'
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
    return tempfile.mkdtemp(prefix="otrp-world-")


def write_tool(world, name, body):
    path = os.path.join(world, name)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    return path


def run_cli(cwd, args):
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.Popen([sys.executable, MODULE] + args, cwd=cwd,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=env)
    out, err = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace"), \
        err.decode("utf-8", "replace")


def law_module():
    import owner_table_parity
    return owner_table_parity


def wire_module():
    import owner_table_usage_wire
    return owner_table_usage_wire


def ac_otrp1():
    """Both readings are asked at call time: patching either one moves rows."""
    world = make_world()
    write_tool(world, "tool.py", LAW_ONLY_TOOL)
    baseline = OTRP.audit(world)
    law = law_module()
    wire = wire_module()
    original_law_audit = law.audit
    original_wire_audit = wire.audit
    law_face = law.audit(os.path.join(world, "tool.py"))
    wire_face = wire.audit(os.path.join(world, "tool.py"))
    try:
        law.audit = lambda path: dict(wire_face)
        patched_law = OTRP.audit(world)
    finally:
        law.audit = original_law_audit
    try:
        wire.audit = lambda path: dict(law_face)
        patched_wire = OTRP.audit(world)
    finally:
        wire.audit = original_wire_audit
    restored = OTRP.audit(world)
    shutil.rmtree(world, ignore_errors=True)
    moved = (len(baseline["rows"]) == 1
             and len(patched_law["rows"]) == 0
             and len(patched_wire["rows"]) == 0
             and len(restored["rows"]) == 1)
    if not moved:
        print("  measured: baseline=%r patched_law=%r patched_wire=%r "
              "restored=%r" % (len(baseline["rows"]), len(patched_law["rows"]),
                               len(patched_wire["rows"]),
                               len(restored["rows"])), flush=True)
    check(moved, "AC-OTRP1 both readings are asked at call time, so patching "
                 "either shipped reader moves the disagreement list")


def ac_otrp2():
    """Every row names both verdicts; a law-only row carries the law's flags."""
    world = make_world()
    law_only = write_tool(world, "law_only.py", LAW_ONLY_TOOL)
    differs = write_tool(world, "differs.py", TABLES_DIFFER_TOOL)
    payload = OTRP.audit(world)
    rows = dict((row["tool"], row) for row in payload["rows"])
    law = law_module()
    direct = law.audit(law_only)
    direct_flags = sorted(set(direct["missing_in_table"])
                          | set(direct["missing_in_parser"]))
    row = rows.get("law_only.py")
    both_named = row is not None and row["law"] == law.VERDICT_DISAGREES and \
        row["wire"] == OTP.VERDICT_NO_TABLE
    reason_ok = row is not None and row["reason"] == OTRP.REASON_LAW_ONLY
    flags_ok = row is not None and row["flags"] == direct_flags and \
        row["flags"] != []
    differs_row = rows.get("differs.py")
    differs_ok = (differs_row is not None
                  and differs_row["reason"] == OTRP.REASON_TABLE_DIFFERS
                  and differs_row["law"] != differs_row["wire"]
                  and set(OTRP.ROW_KEYS) == set(differs_row))
    keys_ok = all(set(row.keys()) == set(OTRP.ROW_KEYS)
                  for row in payload["rows"])
    ok = both_named and reason_ok and flags_ok and differs_ok and keys_ok
    if not ok:
        print("  measured: row=%r direct_flags=%r differs=%r keys_ok=%r"
              % (row, direct_flags, differs_row, keys_ok), flush=True)
    shutil.rmtree(world, ignore_errors=True)
    check(ok, "AC-OTRP2 every row names both verdicts and a law-only row "
              "carries the flags the law itself reported")


def ac_otrp3():
    """Agreement reads CLEAN at exit 0; any disagreement reads SPLIT at exit 2."""
    clean_world = make_world()
    write_tool(clean_world, "agrees.py", AGREES_TOOL)
    write_tool(clean_world, "bare.py", BARE_TOOL)
    clean_payload = OTRP.audit(clean_world)
    rc_clean, out_clean, _ = run_cli(clean_world, [clean_world])
    split_world = make_world()
    write_tool(split_world, "agrees.py", AGREES_TOOL)
    write_tool(split_world, "law_only.py", LAW_ONLY_TOOL)
    split_payload = OTRP.audit(split_world)
    rc_split, out_split, _ = run_cli(split_world, [split_world])
    shutil.rmtree(clean_world, ignore_errors=True)
    shutil.rmtree(split_world, ignore_errors=True)
    ok = (clean_payload["verdict"] == OTRP.VERDICT_CLEAN
          and clean_payload["rows"] == [] and clean_payload["split"] == 0
          and rc_clean == 0 and "verdict=PARITY-CLEAN" in out_clean
          and split_payload["verdict"] == OTRP.VERDICT_SPLIT
          and split_payload["split"] == 1
          and rc_split == 2 and "verdict=PARITY-SPLIT" in out_split)
    if not ok:
        print("  measured: clean=%r rc=%r split=%r rc=%r"
              % (clean_payload["verdict"], rc_clean,
                 split_payload["verdict"], rc_split), flush=True)
    check(ok, "AC-OTRP3 an agreeing tree reads PARITY-CLEAN at exit 0 and a "
              "disagreeing one reads PARITY-SPLIT at exit 2")


def ac_otrp4():
    """The per-round family is superseded by its base, derived, not whitelisted."""
    world = make_world()
    write_tool(world, "battery_followup.py", BARE_TOOL)
    write_tool(world, "battery_followup_R2001.py", LAW_ONLY_TOOL)
    with_base = OTRP.audit(world)
    os.remove(os.path.join(world, "battery_followup.py"))
    without_base = OTRP.audit(world)
    shutil.rmtree(world, ignore_errors=True)
    with io.open(MODULE, encoding="utf-8") as handle:
        text = handle.read()
    tree = ast.parse(text)
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef,
                             ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and \
                    isinstance(body[0].value, ast.Constant) and \
                    isinstance(body[0].value.value, str):
                docstrings.add(id(body[0].value))
    data_strings = [node.value for node in ast.walk(tree)
                    if isinstance(node, ast.Constant)
                    and isinstance(node.value, str)
                    and id(node) not in docstrings]
    no_family_name = not any("battery_followup" in value
                             for value in data_strings)
    no_whitelist = "WHITELIST" not in text
    ok = (len(with_base["rows"]) == 1
          and with_base["superseded"] == 1 and with_base["split"] == 0
          and with_base["verdict"] == OTRP.VERDICT_CLEAN
          and len(without_base["rows"]) == 1
          and without_base["superseded"] == 0 and without_base["split"] == 1
          and without_base["verdict"] == OTRP.VERDICT_SPLIT
          and no_family_name and no_whitelist)
    if not ok:
        print("  measured: with_base=%r without_base=%r no_family_name=%r "
              "no_whitelist=%r" % (with_base["superseded"], 
                                   without_base["superseded"],
                                   no_family_name, no_whitelist), flush=True)
    check(ok, "AC-OTRP4 a per-round copy is superseded only while its base "
              "callable sits beside it, and no tool name is hard-coded")


def ac_otrp5():
    """Exits 0/2/3/5 and a byte-stable --json over pinned keys."""
    clean_world = make_world()
    write_tool(clean_world, "agrees.py", AGREES_TOOL)
    split_world = make_world()
    write_tool(split_world, "law_only.py", LAW_ONLY_TOOL)
    rc_clean, _, _ = run_cli(clean_world, [clean_world])
    rc_split, _, _ = run_cli(split_world, [split_world])
    rc_missing, _, _ = run_cli(clean_world,
                               [os.path.join(clean_world, "absent")])
    rc_bad, _, _ = run_cli(clean_world, ["--nope"])
    first = run_cli(clean_world, [clean_world, "--json"])[1]
    second = run_cli(clean_world, [clean_world, "--json"])[1]
    stable = first == second and first.strip() != ""
    keys = list(json.loads(first).keys()) if stable else []
    shutil.rmtree(clean_world, ignore_errors=True)
    shutil.rmtree(split_world, ignore_errors=True)
    ok = (rc_clean == 0 and rc_split == 2 and rc_missing == 3
          and rc_bad == 5 and stable
          and keys == sorted(list(OTRP.JSON_KEYS)))
    if not ok:
        print("  measured: codes=(%r,%r,%r,%r) stable=%r keys=%r"
              % (rc_clean, rc_split, rc_missing, rc_bad, stable, keys),
              flush=True)
    check(ok, "AC-OTRP5 exits are 0/2/3/5 and --json is byte-stable over the "
              "pinned key set")


def ac_otrp6():
    """Pure ASCII stdlib, no clock, no network, read-only, label wired."""
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
    no_write = (".write(" not in body and "os.replace" not in body
                and "os.remove" not in body and "tempfile" not in body
                and "shutil" not in body and "open(" not in body)
    no_clock = ("time" not in imported and "datetime" not in imported
                and "os.utime" not in body)
    # "stdlib only" means no third-party and no network dependency: the two
    # non-stdlib names are the shipped readers this module asks at call time,
    # which AC-OTRP1 requires and which live in this tree.
    ok = (all(byte < 128 for byte in raw)
          and imported <= {"json", "os", "re", "sys", "owner_table_parity",
                           "owner_table_usage_wire"}
          and "socket" not in body and "urllib" not in body
          and "requests" not in body
          and no_write and no_clock
          and WIRED_EXPECT in runner
          and ('"%s"' % LABEL) in runner)
    if not ok:
        print("  measured: ascii=%r imports=%r no_write=%r no_clock=%r "
              "wired=%r label=%r"
              % (all(byte < 128 for byte in raw), sorted(imported), no_write,
                 no_clock, WIRED_EXPECT in runner,
                 ('"%s"' % LABEL) in runner), flush=True)
    check(ok, "AC-OTRP6 pure ASCII stdlib, no clock, no network, read-only, "
              "and its own reconcile label is wired into the runner")


def main():
    ac_otrp1()
    ac_otrp2()
    ac_otrp3()
    ac_otrp4()
    ac_otrp5()
    ac_otrp6()
    print("SUMMARY passes=%d fails=%d" % (PASSES, FAILS), flush=True)
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())