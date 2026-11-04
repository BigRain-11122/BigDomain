"""owner_table_split_triage suite (R2436; criteria AC-OTST1..AC-OTST6 pinned
inside the R2412 tech seed row of state/queue/tech.md:500 BEFORE this code).

What this proves: owner_table_reader_parity publishes the split between the
law and the wire, and every round re-reports the same known law false
positives with no way to say reviewed and accepted. This suite proves that the
declaration moves such rows out of the split without hiding them, that a
declaration row which no longer matches is aged into STALE instead of being
silently kept, and that nothing on the read path writes.

  AC-OTST1 the declaration row shape is exactly {tool, reason, since_round}
           and an entry naming no live disagreement reads STALE naming the
           tool rather than being silently kept;
  AC-OTST2 a triaged row is counted TRIAGED and removed from split while still
           printed with both verdicts and the law flags;
  AC-OTST3 an entry for a tool that has become PARITY-AGREES on both sides
           reads STALE, never CLEAN by accident;
  AC-OTST4 verdict CLEAN at exit 0 when every remaining disagreement is
           triaged while any untriaged row keeps SPLIT at exit 2;
  AC-OTST5 the reader writes nothing, the declaration keeps its own line
           endings, and CLI exits 0/2/3/5 with a byte-stable --json over the
           pinned keys;
  AC-OTST6 pure ASCII, stdlib only, zero network, no clock, own reconcile
           label and suite.

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

import owner_table_split_triage as OTST  # noqa: E402

MODULE = os.path.join(BASE, "owner_table_split_triage.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-owner-table-split-triage"
WIRED_EXPECT = '"os-owner-table-split-triage"'

# both readers agree: the table is named by a usage path and the parser
# accepts exactly it, so this tool never becomes a disagreement row.
AGREES_TOOL = (
    'FLAGS = ("--alpha", "--beta")\n'
    '\n'
    'def usage():\n'
    '    print(FLAGS)\n'
    '\n'
    'def main(argv):\n'
    '    for token in argv:\n'
    '        if token == "--alpha":\n'
    '            pass'
    '\n'
    '        if token == "--beta":\n'
    '            pass\n'
    '    return 0\n'
)

# the law reads a module-level vocabulary, the usage wire correctly reads no
# argv table: the one-sided shape the split face publishes.
LAW_ONLY_TOOL = (
    'ARGS = ["--round", "R2001", "--until", "R2002", "--json"]\n'
    '\n'
    'def main(argv):\n'
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
    return tempfile.mkdtemp(prefix="otst-world-")


def write_text(path, body, newline="\n"):
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(body.replace("\n", newline))
    return path


def write_tool(world, name, body):
    return write_text(os.path.join(world, name), body)


def write_declaration(world, entries, newline="\n"):
    body = json.dumps({"entries": entries}, ensure_ascii=True, indent=1) + "\n"
    return write_text(os.path.join(world, "triage.json"), body, newline)


def entry(tool, reason, since_round=2412):
    return {"tool": tool, "reason": reason, "since_round": since_round}


def run_cli(cwd, args):
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.Popen([sys.executable, MODULE] + args, cwd=cwd,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=env)
    out, err = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace"), \
        err.decode("utf-8", "replace")


def live_row(world, name=LAW_ONLY_TOOL):
    """The measured reason of the live row this world produces, or None."""
    payload = OTST.audit(world)
    if payload is None:
        return None
    for row in payload["rows"]:
        if not row["status"] == "SPLIT" and row["tool"] != "law_only.py":
            continue
        return row
    return None


def ac_otst1():
    """Row shape is exactly {tool, reason, since_round}; a dead entry is STALE."""
    world = make_world()
    write_tool(world, "law_only.py", LAW_ONLY_TOOL)
    bad_shapes = [
        {"tool": "law_only.py", "reason": "x"},
        {"tool": "law_only.py", "reason": "x", "since_round": 1,
         "extra": "no"},
        {"tool": "law_only.py", "reason": "   ", "since_round": 1},
        {"tool": "law_only.py", "reason": "x", "since_round": "R2412"},
        {"tool": "", "reason": "x", "since_round": 1},
    ]
    bad_results = []
    for shape in bad_shapes:
        path = write_declaration(world, [shape])
        rc, out, _ = run_cli(world, [world, "--declaration", path])
        bad_results.append((rc, OTST.E_OTST_BAD_DECL in out))
    dead = write_declaration(world, [entry("ghost.py", "accepted")])
    payload = OTST.audit(world, dead)
    stale = payload["stale"]
    ok = (all(rc == 3 and named for rc, named in bad_results)
          and len(stale) == 1
          and stale[0]["tool"] == "ghost.py"
          and stale[0]["why"] == OTST.STALE_NO_LIVE
          and set(stale[0].keys()) == set(OTST.STALE_KEYS)
          and set(OTST.ENTRY_KEYS) == set(["tool", "reason", "since_round"]))
    if not ok:
        print("  measured: bad=%r stale=%r keys=%r"
              % (bad_results, stale, sorted(stale[0].keys()) if stale else []),
              flush=True)
    shutil.rmtree(world, ignore_errors=True)
    check(ok, "AC-OTST1 the declaration row shape is exactly "
              "{tool, reason, since_round} and a dead entry reads STALE")


def ac_otst2():
    """A triaged row leaves split, stays printed with both verdicts and flags."""
    world = make_world()
    write_tool(world, "law_only.py", LAW_ONLY_TOOL)
    row = live_row(world)
    if row is None:
        print("  measured: no live row in the fixture world", flush=True)
        shutil.rmtree(world, ignore_errors=True)
        check(False, "AC-OTST2 a triaged row leaves split and stays printed")
        return
    decl = write_declaration(world, [entry("law_only.py", row["reason"])])
    untriaged = OTST.audit(world)
    triaged = OTST.audit(world, decl)
    printed = [item for item in triaged["rows"] if item["tool"] == "law_only.py"]
    ok = (untriaged["split"] == 1 and untriaged["triaged"] == 0
          and triaged["split"] == 0 and triaged["triaged"] == 1
          and triaged["stale"] == []
          and len(printed) == 1
          and printed[0]["status"] == OTST.STATUS_TRIAGED
          and printed[0]["law"] == "PARITY-DISAGREES"
          and printed[0]["wire"] == "NO-TABLE"
          and printed[0]["flags"] == ["--json", "--round", "--until"]
          and set(printed[0].keys()) == set(OTST.ROW_KEYS))
    if not ok:
        print("  measured: untriaged=%r triaged=%r printed=%r"
              % ((untriaged["split"], untriaged["triaged"]),
                 (triaged["split"], triaged["triaged"]), printed), flush=True)
    shutil.rmtree(world, ignore_errors=True)
    check(ok, "AC-OTST2 a triaged row is counted TRIAGED, leaves split, and "
              "still prints both verdicts plus the law flags")


def ac_otst3():
    """An entry whose tool now agrees on both sides reads STALE."""
    world = make_world()
    write_tool(world, "agrees.py", AGREES_TOOL)
    decl = write_declaration(world, [entry("agrees.py", "law-only-table")])
    payload = OTST.audit(world, decl)
    stale = payload["stale"]
    ok = (payload["verdict"] == OTST.VERDICT_CLEAN
          and payload["rows"] == []
          and len(stale) == 1
          and stale[0]["tool"] == "agrees.py"
          and stale[0]["why"] == OTST.STALE_NO_LIVE)
    if not ok:
        print("  measured: verdict=%r rows=%r stale=%r"
              % (payload["verdict"], payload["rows"], stale), flush=True)
    shutil.rmtree(world, ignore_errors=True)
    check(ok, "AC-OTST3 an entry for a tool that now agrees on both sides "
              "reads STALE, never clean by accident")


def ac_otst4():
    """Every remaining disagreement triaged reads CLEAN at exit 0, else 2."""
    world = make_world()
    write_tool(world, "law_only.py", LAW_ONLY_TOOL)
    row = live_row(world)
    decl = write_declaration(world, [entry("law_only.py", row["reason"])])
    rc_clean, out_clean, _ = run_cli(world, [world, "--declaration", decl])
    write_tool(world, "second.py", (
        'OPTIONS = ["--alpha", "--beta"]\n'
        '\n'
        'def main(argv):\n'
        '    return 0\n'
    ))
    rc_split, out_split, _ = run_cli(world, [world, "--declaration", decl])
    ok = (rc_clean == 0 and "verdict=TRIAGE-CLEAN" in out_clean
          and rc_split == 2 and "verdict=TRIAGE-SPLIT" in out_split
          and "files=[second.py]" in out_split
          and "triaged=1" in out_split)
    if not ok:
        print("  measured: rc_clean=%r out=%r rc_split=%r out=%r"
              % (rc_clean, out_clean.strip(), rc_split,
                 out_split.strip()), flush=True)
    shutil.rmtree(world, ignore_errors=True)
    check(ok, "AC-OTST4 CLEAN at exit 0 when every disagreement is triaged, "
              "SPLIT at exit 2 while any row is untriaged")


def ac_otst5():
    """Read-only over a CRLF declaration, codes 0/2/3/5, byte-stable --json."""
    world = make_world()
    write_tool(world, "law_only.py", LAW_ONLY_TOOL)
    row = live_row(world)
    decl = write_declaration(world, [entry("law_only.py", row["reason"])],
                             newline="\r\n")
    with io.open(decl, "rb") as handle:
        before = handle.read()
    rc_clean, _, _ = run_cli(world, [world, "--declaration", decl])
    with io.open(decl, "rb") as handle:
        after = handle.read()
    write_tool(world, "second.py", (
        'OPTIONS = ["--alpha", "--beta"]\n'
        '\n'
        'def main(argv):\n'
        '    return 0\n'
    ))
    rc_split, _, _ = run_cli(world, [world, "--declaration", decl])
    rc_missing, out_missing, _ = run_cli(
        world, [os.path.join(world, "absent")])
    rc_nodecl, out_nodecl, _ = run_cli(
        world, [world, "--declaration", os.path.join(world, "absent.json")])
    rc_bad, _, _ = run_cli(world, ["--nope"])
    first = run_cli(world, [world, "--json"])[1]
    second = run_cli(world, [world, "--json"])[1]
    stable = first == second and first.strip() != ""
    keys = list(json.loads(first).keys()) if stable else []
    ok = (rc_clean == 0 and rc_split == 2 and rc_missing == 3
          and rc_nodecl == 3 and rc_bad == 5
          and before == after and b"\r\n" in before
          and stable and keys == sorted(list(OTST.JSON_KEYS))
          and OTST.E_OTST_UNREADABLE in out_missing
          and OTST.E_OTST_NO_DECL in out_nodecl)
    if not ok:
        print("  measured: codes=(%r,%r,%r,%r,%r) unchanged=%r crlf=%r "
              "stable=%r keys=%r"
              % (rc_clean, rc_split, rc_missing, rc_nodecl, rc_bad,
                 before == after, b"\r\n" in before, stable, keys), flush=True)
    shutil.rmtree(world, ignore_errors=True)
    check(ok, "AC-OTST5 the reader writes nothing and keeps the declaration's "
              "line endings; exits are 0/2/3/5 and --json is byte-stable")


def ac_otst6():
    """Pure ASCII stdlib, no clock, no network, label wired into the runner."""
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
                and "shutil" not in body)
    no_clock = ("time" not in imported and "datetime" not in imported
                and "os.utime" not in body)
    ok = (all(byte < 128 for byte in raw)
          and imported <= {"io", "json", "os", "sys",
                           "owner_table_reader_parity"}
          and "socket" not in body and "urllib" not in body
          and "requests" not in body
          and no_write and no_clock
          and WIRED_EXPECT in runner
          and '"%s"' % LABEL in runner)
    if not ok:
        print("  measured: ascii=%r imports=%r no_write=%r no_clock=%r "
              "wired=%r label=%r"
              % (all(byte < 128 for byte in raw), sorted(imported), no_write,
                 no_clock, WIRED_EXPECT in runner,
                 ('"%s"' % LABEL) in runner), flush=True)
    check(ok, "AC-OTST6 pure ASCII stdlib, no clock, no network, and its own "
              "reconcile label is wired into the runner")


def main():
    ac_otst1()
    ac_otst2()
    ac_otst3()
    ac_otst4()
    ac_otst5()
    ac_otst6()
    print("SUMMARY passes=%d fails=%d" % (PASSES, FAILS), flush=True)
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())