"""owner_table_triage_expiry suite (R2438; criteria AC-OTTE1..AC-OTTE6 pinned
inside the R2412 tech seed row of state/queue/tech.md:502 BEFORE this code).

What this proves: owner_table_split_triage records since_round on every
acceptance but MEASURED nothing ages it, so an acceptance written at R2436 and
one accepted a year earlier read identically. This suite proves the age is
measured against the supplied round, that the boundary is exact, that a dead
entry is never aged, and that a future date fails closed instead of printing a
negative age.

  AC-OTTE1 every TRIAGED row is aged as current_round minus since_round, keeps
           status TRIAGED and still prints both verdicts and the law flags;
  AC-OTTE2 the boundary is exact: age == window reads FRESH and age ==
           window + 1 reads AGED, with the age printed in rounds;
  AC-OTTE3 an entry with no live row is unageable and never counted, and a
           since_round later than the round fails closed at exit 3;
  AC-OTTE4 EXPIRY-AGED at exit 2 when any row is aged, EXPIRY-CLEAN at 0
           otherwise, and a missing --round reads E_OTTE_NO_ROUND at exit 3;
  AC-OTTE5 the face writes nothing, keeps the declaration's CRLF, exits
           0/2/3/5 and --json is byte-stable over the pinned keys;
  AC-OTTE6 pure ASCII, stdlib only, zero network, no clock, own reconcile
           label wired into the runner.

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

import owner_table_triage_expiry as OTTE  # noqa: E402
import owner_table_split_triage as OTST  # noqa: E402

MODULE = os.path.join(BASE, "owner_table_triage_expiry.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-owner-table-triage-expiry"
WIRED_EXPECT = '"os-owner-table-triage-expiry"'

# The measured one-sided shape: the law reads a module-level argv vocabulary
# the wire never uses as argv, so this tool becomes a live SPLIT row.
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
    return tempfile.mkdtemp(prefix="otte-world-")


def write_text(path, body, newline="\n"):
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(body.replace("\n", newline))
    return path


def write_tool(world, name, body):
    return write_text(os.path.join(world, name), body)


def write_declaration(world, entries, newline="\n"):
    body = json.dumps({"entries": entries}, ensure_ascii=True, indent=1) + "\n"
    return write_text(os.path.join(world, "triage.json"), body, newline)


def entry(tool, reason, since_round=2400):
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


def live_row(world):
    """The measured live disagreement row this world produces, or None."""
    payload = OTST.audit(world)
    if payload is None:
        return None
    for row in payload["rows"]:
        if row["status"] == OTST.STATUS_SPLIT:
            return row
    return None


def ac_otte1():
    """Every triaged row is aged and still prints as TRIAGED with both faces."""
    world = make_world()
    write_tool(world, "law_only.py", LAW_ONLY_TOOL)
    row = live_row(world)
    if row is None:
        print("  measured: no live row in the fixture world", flush=True)
        shutil.rmtree(world, ignore_errors=True)
        check(False, "AC-OTTE1 a triaged row is aged and keeps TRIAGED")
        return
    decl = write_declaration(world, [entry("law_only.py", row["reason"],
                                           since_round=2400)])
    payload = OTTE.audit(world, decl, current_round=2438, window=30)
    printed = payload["rows"]
    ok = (len(printed) == 1
          and printed[0]["status"] == OTST.STATUS_TRIAGED
          and printed[0]["age_status"] == OTTE.STATUS_AGED
          and printed[0]["age_rounds"] == 38
          and printed[0]["since_round"] == 2400
          and printed[0]["law"] == "PARITY-DISAGREES"
          and printed[0]["wire"] == "NO-TABLE"
          and printed[0]["flags"] == ["--json", "--round", "--until"]
          and payload["triaged"] == 1 and payload["aged"] == 1
          and payload["fresh"] == 0
          and set(printed[0].keys()) == set(OTTE.AGED_KEYS)
          and set(payload.keys()) == set(OTTE.JSON_KEYS))
    if not ok:
        print("  measured: printed=%r payload=%r" % (printed, sorted(
            payload.keys())), flush=True)
    shutil.rmtree(world, ignore_errors=True)
    check(ok, "AC-OTTE1 age is measured as current_round minus since_round and "
              "the row keeps status TRIAGED printing both verdicts")


def ac_otte2():
    """The window boundary is exact (age == window FRESH, +1 AGED)."""
    world = make_world()
    write_tool(world, "law_only.py", LAW_ONLY_TOOL)
    row = live_row(world)
    decl = write_declaration(world, [entry("law_only.py", row["reason"],
                                           since_round=2400)])
    at_edge = OTTE.audit(world, decl, current_round=2430, window=30)
    past_edge = OTTE.audit(world, decl, current_round=2431, window=30)
    zero_edge = OTTE.audit(world, decl, current_round=2400, window=30)
    ok = (at_edge["rows"][0]["age_rounds"] == 30
          and at_edge["rows"][0]["age_status"] == OTTE.STATUS_FRESH
          and at_edge["fresh"] == 1 and at_edge["aged"] == 0
          and at_edge["verdict"] == OTTE.VERDICT_CLEAN
          and past_edge["rows"][0]["age_rounds"] == 31
          and past_edge["rows"][0]["age_status"] == OTTE.STATUS_AGED
          and past_edge["aged"] == 1
          and past_edge["verdict"] == OTTE.VERDICT_AGED
          and zero_edge["rows"][0]["age_rounds"] == 0
          and zero_edge["rows"][0]["age_status"] == OTTE.STATUS_FRESH)
    if not ok:
        print("  measured: at=%r past=%r zero=%r"
              % (at_edge["rows"], past_edge["rows"], zero_edge["rows"]),
              flush=True)
    shutil.rmtree(world, ignore_errors=True)
    check(ok, "AC-OTTE2 age == window reads FRESH and age == window + 1 reads "
              "AGED")


def ac_otte3():
    """A dead entry is unageable; a future since_round fails closed."""
    world = make_world()
    write_tool(world, "law_only.py", LAW_ONLY_TOOL)
    row = live_row(world)
    ghost = write_declaration(world, [
        entry("law_only.py", row["reason"], since_round=2400),
        entry("ghost.py", "accepted", since_round=2390),
    ])
    payload = OTTE.audit(world, ghost, current_round=2438, window=30)
    unageable = payload["unageable"]
    future = write_declaration(world, [entry("law_only.py", row["reason"],
                                             since_round=2500)])
    rc_future, out_future, _ = run_cli(
        world, [world, "--declaration", future, "--round", "2438"])
    ok = (len(unageable) == 1
          and unageable[0]["tool"] == "ghost.py"
          and unageable[0]["why"] == OTTE.UNAGEABLE_NO_LIVE
          and set(unageable[0].keys()) == set(OTTE.UNAGEABLE_KEYS)
          and payload["triaged"] == 1 and payload["aged"] == 1
          and rc_future == 3 and OTTE.E_OTTE_FUTURE in out_future)
    if not ok:
        print("  measured: unageable=%r rc_future=%r out=%r"
              % (unageable, rc_future, out_future.strip()), flush=True)
    shutil.rmtree(world, ignore_errors=True)
    check(ok, "AC-OTTE3 a dead entry is unageable, never aged, and a future "
              "since_round fails closed")


def ac_otte4():
    """Verdicts and exits: 2 when aged, 0 when fresh, 3 without a round."""
    world = make_world()
    write_tool(world, "law_only.py", LAW_ONLY_TOOL)
    row = live_row(world)
    decl = write_declaration(world, [entry("law_only.py", row["reason"],
                                           since_round=2400)])
    rc_aged, out_aged, _ = run_cli(
        world, [world, "--declaration", decl, "--round", "2438"])
    rc_fresh, out_fresh, _ = run_cli(
        world, [world, "--declaration", decl, "--round", "2410"])
    rc_noround, out_noround, _ = run_cli(
        world, [world, "--declaration", decl])
    rc_badround, out_badround, _ = run_cli(
        world, [world, "--declaration", decl, "--round", "nope"])
    ok = (rc_aged == 2 and "verdict=EXPIRY-AGED" in out_aged
          and "aged=[law_only.py(38)]" in out_aged
          and rc_fresh == 0 and "verdict=EXPIRY-CLEAN" in out_fresh
          and "fresh=[law_only.py(10)]" in out_fresh
          and rc_noround == 3 and OTTE.E_OTTE_NO_ROUND in out_noround
          and rc_badround == 3 and OTTE.E_OTTE_BAD_ROUND in out_badround)
    if not ok:
        print("  measured: aged=(%r,%r) fresh=(%r,%r) noround=(%r,%r) "
              "badround=(%r,%r)"
              % (rc_aged, out_aged.strip(), rc_fresh, out_fresh.strip(),
                 rc_noround, out_noround.strip(), rc_badround,
                 out_badround.strip()), flush=True)
    shutil.rmtree(world, ignore_errors=True)
    check(ok, "AC-OTTE4 EXPIRY-AGED at exit 2, EXPIRY-CLEAN at 0, and a "
              "missing or bad --round reads exit 3 rather than a clock")


def ac_otte5():
    """Read-only over a CRLF declaration, codes 0/2/3/5, byte-stable --json."""
    world = make_world()
    write_tool(world, "law_only.py", LAW_ONLY_TOOL)
    row = live_row(world)
    decl = write_declaration(world, [entry("law_only.py", row["reason"],
                                           since_round=2400)],
                             newline="\r\n")
    with io.open(decl, "rb") as handle:
        before = handle.read()
    rc_clean, _, _ = run_cli(
        world, [world, "--declaration", decl, "--round", "2410"])
    rc_aged, _, _ = run_cli(
        world, [world, "--declaration", decl, "--round", "2438"])
    with io.open(decl, "rb") as handle:
        after = handle.read()
    rc_missing, out_missing, _ = run_cli(
        world, [os.path.join(world, "absent"), "--round", "2438"])
    rc_nodecl, out_nodecl, _ = run_cli(
        world, [world, "--declaration", os.path.join(world, "absent.json"),
                "--round", "2438"])
    rc_bad, _, _ = run_cli(world, ["--nope"])
    first = run_cli(world, [world, "--declaration", decl, "--round", "2438",
                            "--json"])[1]
    second = run_cli(world, [world, "--declaration", decl, "--round", "2438",
                             "--json"])[1]
    stable = first == second and first.strip() != ""
    keys = list(json.loads(first).keys()) if stable else []
    ok = (rc_clean == 0 and rc_aged == 2 and rc_missing == 3
          and rc_nodecl == 3 and rc_bad == 5
          and before == after and b"\r\n" in before
          and stable and keys == sorted(list(OTTE.JSON_KEYS))
          and OTTE.E_OTTE_UNREADABLE in out_missing
          and OTST.E_OTST_NO_DECL in out_nodecl)
    if not ok:
        print("  measured: codes=(%r,%r,%r,%r,%r) unchanged=%r crlf=%r "
              "stable=%r keys=%r"
              % (rc_clean, rc_aged, rc_missing, rc_nodecl, rc_bad,
                 before == after, b"\r\n" in before, stable, keys), flush=True)
    shutil.rmtree(world, ignore_errors=True)
    check(ok, "AC-OTTE5 the face writes nothing and keeps the declaration's "
              "line endings; exits are 0/2/3/5 and --json is byte-stable")


def ac_otte6():
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
                and "os.utime" not in body and "time.time" not in body)
    ok = (all(byte < 128 for byte in raw)
          and imported <= {"io", "json", "os", "sys",
                           "owner_table_split_triage"}
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
    check(ok, "AC-OTTE6 pure ASCII stdlib, no clock, no network, and its own "
              "reconcile label is wired into the runner")


def main():
    ac_otte1()
    ac_otte2()
    ac_otte3()
    ac_otte4()
    ac_otte5()
    ac_otte6()
    print("SUMMARY passes=%d fails=%d" % (PASSES, FAILS), flush=True)
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())