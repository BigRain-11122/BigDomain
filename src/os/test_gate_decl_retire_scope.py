"""gate_decl_retire_scope suite (R2321; criteria AC-GDRTS1..AC-GDRTS6 were
pre-registered inside the R2319 seed row of state/queue/tech.md BEFORE this
code existed).

What this proves: the retire wire refused every MATCHED identity, so a
declared blocker whose row was COMPLETED could never be retired (AC-GDRTW3
measured the gated fixture and the done fixture refusing identically). This
scope reading hands gate_decl_retire only the cases it should own - a matched
DONE row and an UNMATCHED identity - while a matched OPEN or GATED row refuses
before any byte with its level named, and AMBIGUOUS keeps refusing with every
carrier. The suite proves both imports by patching each side and watching the
verdict move, and proves there is no second queue scan.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import gate_decl_identity as GDI  # noqa: E402
import gate_decl_retire as GDRT  # noqa: E402
import gate_decl_retire_scope as GDRTS  # noqa: E402
import machine_gate as MG  # noqa: E402
import queue_row as QR  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "gate_decl_retire_scope.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-gate-decl-retire-scope"

HEADER = "# queue test world\n\nprose that never becomes a row\n\n"
ROW_GATED = "- [ ] docker sandbox row, blocked on CEO merchant number: AC-GAT1 pinned"
ROW_DONE = "- [x] [done 2026-11-01 R2300] closed row: AC-DON1 pinned"
ROW_OPEN = "- [ ] open product row: Criteria prefix AC-OPE1 pinned here"
ROW_DUP = "- [ ] duplicated row: AC-DUP1 pinned here"

MISSING_ID = "AC-NONE1#deadbeef"

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


def identity_of_row(line):
    """The identity a row carries, read through the module's own law."""
    return MG.identity_of(QR.scan_row(line)["prefix"], line)


def declaration(identities, capability="docker"):
    """A declaration body carrying one entry per identity."""
    gates = [{"identity": identity,
              "capability": capability,
              "reason": "suite declaration",
              "declared_by": "R2321"} for identity in identities]
    return {"version": 1,
            "declared_by": "R2321",
            "reason": "suite declaration",
            "gates": gates}


def make_world(tech=None, decl=None, write_decl=True):
    """Build a temp root with the three queue files and one declaration."""
    world = tempfile.mkdtemp(prefix="bigdomain-gdrts-")
    queue = os.path.join(world, "state", "queue")
    os.makedirs(queue)
    bodies = {"tech": tech if tech is not None else HEADER,
              "main": HEADER, "explore": HEADER}
    for name, body in bodies.items():
        with io.open(os.path.join(queue, "%s.md" % name), "w",
                     encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    if write_decl:
        path = os.path.join(world, MG.DEFAULT_DECLARATION)
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(decl if decl is not None
                                    else declaration([]), indent=2))
    return world


def decl_path(world):
    return os.path.join(world, MG.DEFAULT_DECLARATION)


def decl_bytes(world):
    with open(decl_path(world), "rb") as handle:
        return handle.read()


def tree_digest(root):
    """A digest over every file under root, so a write cannot hide."""
    import hashlib
    digest = hashlib.sha256()
    for base, _dirs, files in os.walk(root):
        for name in sorted(files):
            path = os.path.join(base, name)
            digest.update(os.path.relpath(path, root).encode("utf-8"))
            with open(path, "rb") as handle:
                digest.update(handle.read())
    return digest.hexdigest()


def run_cli(world, args):
    """Run the module CLI in the world and return (rc, stdout)."""
    env = dict(os.environ)
    env["PYTHONPATH"] = BASE
    proc = subprocess.run([sys.executable, MODULE] + list(args)
                          + ["--root", world],
                          cwd=world, env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


WORLD_ROWS = HEADER + "\n".join([ROW_GATED, ROW_DONE, ROW_OPEN, ROW_DUP,
                                 ROW_DUP]) + "\n"

OPEN_ID = identity_of_row(ROW_OPEN)
GATED_ID = identity_of_row(ROW_GATED)
DONE_ID = identity_of_row(ROW_DONE)
DUP_ID = identity_of_row(ROW_DUP)


def refusal(func, *args, **kwargs):
    """Run one call and return (code, detail) or (None, None)."""
    try:
        func(*args, **kwargs)
    except GDRTS.ScopeError as exc:
        return exc.code, exc.detail
    return None, None


def ac_gdrts1():
    """Both laws are imported: patching either side moves the verdict."""
    world = make_world(tech=WORLD_ROWS,
                       decl=declaration([MISSING_ID, DONE_ID]))
    try:
        report = GDRTS.plan(world, MISSING_ID)
        planned = report["verdict"] == GDRTS.VERDICT_PLANNED
        live_done = GDRTS.plan(world, DONE_ID)
        done_allowed = (live_done["scope"] == GDRTS.SCOPE_ALLOWED
                        and live_done["level"] == "done")

        original_resolve = GDI.resolve

        def patched_resolve(identity, rows_found):
            return {"state": "MATCHED", "line": 9, "prefix": "AC-OPE1",
                    "level": "open", "claimable": True,
                    "detail": "patched reader", "carriers": []}

        GDI.resolve = patched_resolve
        try:
            code_reader, _ = refusal(GDRTS.plan, world, MISSING_ID)
            reader_moved = code_reader == "E_GDRTS_MATCHED"
        finally:
            GDI.resolve = original_resolve

        original_retire = GDRT.retire

        def patched_retire(root, identity, queue_name="tech",
                           declaration=None, execute=False):
            return {"path": "state/machine_gates.json", "identity": identity,
                    "capability": "docker", "removed_at": 0,
                    "declarations_before": 1, "declarations_after": 0,
                    "before_bytes": 1, "predicted_bytes": 1,
                    "wrote": False, "read_back_ok": None,
                    "verdict": "PLANNED"}

        GDRT.retire = patched_retire
        try:
            patched = GDRTS.plan(world, MISSING_ID)
            plan_moved = (patched["verdict"] == GDRTS.VERDICT_PLANNED
                          and patched["predicted_bytes"] == 1)
        finally:
            GDRT.retire = original_retire

        original_rows = GDI.rows
        GDI.rows = lambda root, name="tech": []
        try:
            rows_report = GDRTS.plan(world, DONE_ID)
            # With no rows at all the done identity no longer resolves, so the
            # plan layer answers instead - the stronger proof that rows moved.
            rows_moved = rows_report["state"] == "UNMATCHED"
        finally:
            GDI.rows = original_rows

        source = io.open(MODULE, "r", encoding="utf-8").read()
        no_second_scan = (
            not re.search(r"^\s*(?:import|from)\s+queue_head", source, re.M)
            and not re.search(r"open\([^)\n]*queue", source)
            and "import gate_decl_identity as GDI" in source
            and "import gate_decl_retire as GDRT" in source)
        ok = (planned and done_allowed and reader_moved and plan_moved
              and rows_moved and no_second_scan)
        if not ok:
            print("  measured: planned=%r done=%r reader=%r plan=%r rows=%r "
                  "scan=%r"
                  % (planned, done_allowed, reader_moved, plan_moved,
                     rows_moved, no_second_scan), flush=True)
        check(ok, "AC-GDRTS1 both laws imported, neither re-implemented")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_gdrts2():
    """A matched DONE row reaches the plan; open and gated refuse by level."""
    world = make_world(tech=WORLD_ROWS,
                       decl=declaration([DONE_ID, OPEN_ID, GATED_ID]))
    try:
        before = decl_bytes(world)
        plan = GDRTS.plan(world, DONE_ID)
        done_ok = (plan["scope"] == GDRTS.SCOPE_ALLOWED
                   and plan["state"] == "MATCHED"
                   and plan["level"] == "done"
                   and plan["verdict"] == GDRTS.VERDICT_PLANNED
                   and plan["declarations_before"] == 3
                   and plan["declarations_after"] == 2)
        mid = decl_bytes(world)

        code_open, detail_open = refusal(GDRTS.plan, world, OPEN_ID)
        open_ok = (code_open == "E_GDRTS_MATCHED" and "open" in detail_open)

        code_gated, detail_gated = refusal(GDRTS.plan, world, GATED_ID)
        gated_ok = (code_gated == "E_GDRTS_MATCHED" and "gated" in detail_gated)

        after = decl_bytes(world)
        ok = (done_ok and open_ok and gated_ok and before == mid == after)
        if not ok:
            print("  measured: done=%r open=%r/%r gated=%r/%r same=%r"
                  % (done_ok, code_open, detail_open, code_gated, detail_gated,
                     before == mid == after), flush=True)
        check(ok, "AC-GDRTS2 done row retires, open and gated refuse by level")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_gdrts3():
    """AMBIGUOUS names every carrier; UNMATCHED still reaches the plan."""
    world = make_world(tech=WORLD_ROWS,
                       decl=declaration([DUP_ID, MISSING_ID]))
    try:
        before = tree_digest(world)
        code_a, detail_a = refusal(GDRTS.plan, world, DUP_ID)
        ambiguous_ok = (code_a == "E_GDRTS_AMBIGUOUS"
                        and "AMBIGUOUS" in detail_a
                        and "L8" in detail_a and "L9" in detail_a)
        mid = tree_digest(world)
        plan = GDRTS.plan(world, MISSING_ID)
        unmatched_ok = (plan["state"] == "UNMATCHED"
                        and plan["scope"] == GDRTS.SCOPE_ALLOWED
                        and plan["verdict"] == GDRTS.VERDICT_PLANNED)
        ok = ambiguous_ok and unmatched_ok and before == mid
        if not ok:
            print("  measured: ambiguous=%r/%r unmatched=%r same=%r"
                  % (code_a, detail_a, unmatched_ok, before == mid),
                  flush=True)
        check(ok, "AC-GDRTS3 AMBIGUOUS keeps refusing, UNMATCHED still plans")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_gdrts4():
    """The success path is byte-identical to gate_decl_retire's own retire."""
    world = make_world(tech=WORLD_ROWS,
                       decl=declaration([MISSING_ID, DONE_ID, GATED_ID]))
    twin = make_world(tech=WORLD_ROWS,
                      decl=declaration([MISSING_ID, DONE_ID, GATED_ID]))
    try:
        wired_exec = GDRTS.plan(world, DONE_ID, execute=True)
        direct_exec = GDRT.retire(twin, DONE_ID, execute=True)
        same_bytes = decl_bytes(world) == decl_bytes(twin)
        same_verdict = (wired_exec["verdict"] == GDRTS.VERDICT_RETIRED
                        and wired_exec["read_back_ok"] is True
                        and direct_exec["verdict"] == "RETIRED")
        counts = (wired_exec["declarations_before"],
                  wired_exec["declarations_after"])
        survived = decl_bytes(world)
        ok = (same_bytes and same_verdict and counts == (3, 2)
              and survived.count(b'"identity"') == 2
              and GATED_ID.encode("utf-8") in survived
              and MISSING_ID.encode("utf-8") in survived
              and DONE_ID.encode("utf-8") not in survived)
        if not ok:
            print("  measured: bytes=%r verdict=%r counts=%r intact=%r"
                  % (same_bytes, same_verdict, counts,
                     survived.count(b'"identity"')), flush=True)
        check(ok, "AC-GDRTS4 success path byte-identical to the direct retire")
    finally:
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(twin, ignore_errors=True)


def ac_gdrts5():
    """CLI codes 0/2/3/5 and one byte-stable pinned JSON."""
    world = make_world(tech=WORLD_ROWS,
                       decl=declaration([DONE_ID, OPEN_ID]))
    nodecl = make_world(tech=WORLD_ROWS, decl=declaration([DONE_ID]))
    try:
        os.remove(decl_path(nodecl))
        rc_plan, _ = run_cli(world, ["--identity", DONE_ID])
        rc_refuse, _ = run_cli(world, ["--identity", OPEN_ID])
        rc_nodecl, _ = run_cli(nodecl, ["--identity", DONE_ID])
        rc_flags, _ = run_cli(world, ["--identity"])
        json_a, body_a = run_cli(world, ["--identity", DONE_ID, "--json"])
        json_b, body_b = run_cli(world, ["--identity", DONE_ID, "--json"])
        parsed = json.loads(body_a)
        ok = (rc_plan == 0 and rc_refuse == 2 and rc_nodecl == 3
              and rc_flags == 5 and json_a == 0 and json_b == 0
              and body_a == body_b
              and tuple(parsed.keys()) == GDRTS.REPORT_KEYS
              and parsed["verdict"] == GDRTS.VERDICT_PLANNED
              and parsed["scope"] == GDRTS.SCOPE_ALLOWED
              and parsed["level"] == "done")
        if not ok:
            print("  measured: rc=%r/%r/%r/%r json=%r keys=%r"
                  % (rc_plan, rc_refuse, rc_nodecl, rc_flags, json_a,
                     tuple(parsed.keys())), flush=True)
        check(ok, "AC-GDRTS5 CLI codes and a byte-stable pinned JSON")
    finally:
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(nodecl, ignore_errors=True)


def ac_gdrts6():
    """Pure ASCII, no network, no clock, wired in the runner, writes nothing."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = not re.search(r"\b(?:socket|urllib|http)\b", source)
    no_clock = not re.search(r"\b(?:import time|import datetime|time\.time)\b",
                             source)
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner
             and "test_gate_decl_retire_scope.py" in runner)
    world = make_world(tech=WORLD_ROWS, decl=declaration([DONE_ID]))
    try:
        before = tree_digest(world)
        GDRTS.plan(world, DONE_ID)
        after = tree_digest(world)
        ok = ascii_only and no_net and no_clock and wired and before == after
        if not ok:
            print("  measured: ascii=%r net=%r clock=%r wired=%r writes=%r"
                  % (ascii_only, no_net, no_clock, wired, before == after),
                  flush=True)
        check(ok, "AC-GDRTS6 pure, wired, and writes nothing on a dry run")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def main():
    print("gate_decl_retire_scope suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_gdrts1()
    ac_gdrts2()
    ac_gdrts3()
    ac_gdrts4()
    ac_gdrts5()
    ac_gdrts6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())