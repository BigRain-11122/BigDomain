"""gate_decl_retire_wire suite (R2319; criteria AC-GDRTW1..AC-GDRTW6 were
pre-registered inside the R2317 seed row of state/queue/tech.md BEFORE this
code existed).

What this proves: the retirement writer no longer asks only machine_gate's
candidate reading. The identity is resolved through gate_decl_identity's rows
and resolve imports, only an UNMATCHED identity reaches gate_decl_retire, and
MATCHED / AMBIGUOUS are refused before any byte changes with the reader state
and every carrier line in the detail. The suite proves the import by patching
each side and watching the verdict move, and proves there is no second address
scan by patching rows to an empty reading.

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
import gate_decl_retire_wire as GDRTW  # noqa: E402
import machine_gate as MG  # noqa: E402
import queue_row as QR  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "gate_decl_retire_wire.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-gate-decl-retire-wire"

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
              "declared_by": "R2319"} for identity in identities]
    return {"version": 1,
            "declared_by": "R2319",
            "reason": "suite declaration",
            "gates": gates}


def make_world(tech=None, decl=None, write_decl=True):
    """Build a temp root with the three queue files and one declaration."""
    world = tempfile.mkdtemp(prefix="bigdomain-gdrtw-")
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
DUP_ID = identity_of_row(ROW_DUP)


def refusal(func, *args, **kwargs):
    """Run one call and return (code, detail) or (None, None)."""
    try:
        func(*args, **kwargs)
    except GDRTW.WireError as exc:
        return exc.code, exc.detail
    return None, None


def ac_gdrtw1():
    """Both laws are imported: patching either side moves the verdict."""
    world = make_world(tech=WORLD_ROWS,
                       decl=declaration([MISSING_ID, OPEN_ID]))
    try:
        report = GDRTW.plan(world, MISSING_ID)
        planned = report["verdict"] == GDRTW.VERDICT_PLANNED
        code_live, _ = refusal(GDRTW.plan, world, OPEN_ID)
        live_matched = code_live == "E_GDRTW_MATCHED"

        original_resolve = GDI.resolve
        GDI.resolve = lambda identity, rows_found: {
            "state": "MATCHED", "line": 9, "prefix": "AC-OPE1",
            "level": "open", "claimable": True,
            "detail": "patched reader", "carriers": []}
        try:
            code_reader, _ = refusal(GDRTW.plan, world, MISSING_ID)
            reader_moved = code_reader == "E_GDRTW_MATCHED"
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
            patched = GDRTW.plan(world, MISSING_ID)
            plan_moved = (patched["verdict"] == GDRTW.VERDICT_PLANNED
                          and patched["predicted_bytes"] == 1)
        finally:
            GDRT.retire = original_retire

        original_rows = GDI.rows
        GDI.rows = lambda root, name="tech": []
        try:
            code_rows, _ = refusal(GDRTW.plan, world, OPEN_ID)
            # The wire no longer refuses, so the plan layer answers instead:
            # its own still-blocked law is the proof that rows moved.
            rows_moved = code_rows == "E_GDRT_STILL_BLOCKED"
        finally:
            GDI.rows = original_rows

        source = io.open(MODULE, "r", encoding="utf-8").read()
        no_second_scan = (
            not re.search(r"^\s*(?:import|from)\s+queue_head", source, re.M)
            and not re.search(r"open\([^)\n]*queue", source)
            and "import gate_decl_identity as GDI" in source
            and "import gate_decl_retire as GDRT" in source)
        ok = (planned and live_matched and reader_moved and plan_moved
              and rows_moved and no_second_scan)
        if not ok:
            print("  measured: planned=%r live=%r reader=%r plan=%r rows=%r "
                  "scan=%r"
                  % (planned, live_matched, reader_moved, plan_moved,
                     rows_moved, no_second_scan), flush=True)
        check(ok, "AC-GDRTW1 both laws imported, neither re-implemented")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_gdrtw2():
    """MATCHED and AMBIGUOUS refuse before any byte; UNMATCHED reaches plan."""
    world = make_world(tech=WORLD_ROWS,
                       decl=declaration([OPEN_ID, DUP_ID, GATED_ID,
                                         MISSING_ID]))
    try:
        before = decl_bytes(world)

        code_m, detail_m = refusal(GDRTW.plan, world, OPEN_ID)
        matched_ok = (code_m == "E_GDRTW_MATCHED"
                      and "MATCHED" in detail_m
                      and "carriers none" in detail_m)

        code_a, detail_a = refusal(GDRTW.plan, world, DUP_ID)
        ambiguous_ok = (code_a == "E_GDRTW_AMBIGUOUS"
                        and "AMBIGUOUS" in detail_a
                        and "L8" in detail_a and "L9" in detail_a)
        if not ambiguous_ok:
            print("  measured: ambiguous code=%r detail=%r"
                  % (code_a, detail_a), flush=True)

        mid = decl_bytes(world)
        report = GDRTW.plan(world, MISSING_ID)
        after = decl_bytes(world)
        unmatched_ok = (report["state"] == "UNMATCHED"
                        and report["verdict"] == GDRTW.VERDICT_PLANNED
                        and report["declarations_before"] == 4
                        and report["declarations_after"] == 3)
        ok = (matched_ok and ambiguous_ok and unmatched_ok
              and before == mid == after)
        if not ok:
            print("  measured: m=%r a=%r un=%r same=%r"
                  % (matched_ok, ambiguous_ok, unmatched_ok,
                     before == mid == after), flush=True)
        check(ok, "AC-GDRTW2 MATCHED/AMBIGUOUS refused before any byte")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_gdrtw3():
    """The refusal is the reader's state, and claimability is not the rule."""
    world = make_world(tech=WORLD_ROWS,
                       decl=declaration([GATED_ID, OPEN_ID, DUP_ID]))
    try:
        before = tree_digest(world)
        gated_code, gated_detail = refusal(GDRTW.plan, world, GATED_ID)
        open_code, _ = refusal(GDRTW.plan, world, OPEN_ID)

        reading = GDRTW.resolve_identity(world, GATED_ID)
        gated_level = reading["level"]
        gated_claimable = reading["claimable"]

        # A DONE identity is equally not claimable and must refuse the same way.
        done_id = identity_of_row(ROW_DONE)
        done_world = make_world(tech=WORLD_ROWS, decl=declaration([done_id]))
        try:
            done_code, _ = refusal(GDRTW.plan, done_world, done_id)
        finally:
            shutil.rmtree(done_world, ignore_errors=True)

        after = tree_digest(world)
        ok = (gated_code == "E_GDRTW_MATCHED"
              and gated_level == "gated"
              and gated_claimable is False
              and open_code == "E_GDRTW_MATCHED"
              and done_code == "E_GDRTW_MATCHED"
              and before == after)
        if not ok:
            print("  measured: gated=%r level=%r claimable=%r open=%r "
                  "done=%r writes=%r"
                  % (gated_code, gated_level, gated_claimable, open_code,
                     done_code, before == after), flush=True)
            print("  detail: %s" % gated_detail, flush=True)
        check(ok, "AC-GDRTW3 refusal is the reader's state, not claimability")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_gdrtw4():
    """The success path is byte-identical to gate_decl_retire's own plan."""
    world = make_world(tech=WORLD_ROWS,
                       decl=declaration([MISSING_ID, GATED_ID]))
    twin = make_world(tech=WORLD_ROWS,
                      decl=declaration([MISSING_ID, GATED_ID]))
    try:
        text = io.open(decl_path(world), "r", encoding="utf-8").read()
        live = MG.gate(world, "tech")
        direct = GDRT.plan(text, MISSING_ID, live)

        wired = GDRTW.plan(world, MISSING_ID)
        same_plan = (wired["predicted_bytes"] == direct["predicted_bytes"]
                     and wired["removed_at"] == direct["removed_at"]
                     and wired["declarations_after"]
                     == direct["declarations_after"])

        wired_exec = GDRTW.plan(world, MISSING_ID, execute=True)
        direct_exec = GDRT.retire(twin, MISSING_ID, execute=True)
        same_bytes = decl_bytes(world) == decl_bytes(twin)
        same_verdict = (wired_exec["verdict"] == GDRTW.VERDICT_RETIRED
                        and wired_exec["read_back_ok"] is True
                        and direct_exec["verdict"] == "RETIRED")
        counts = (wired_exec["declarations_before"],
                  wired_exec["declarations_after"])
        ok = (same_plan and same_bytes and same_verdict
              and counts == (2, 1)
              and decl_bytes(world).count(b'"identity"') == 1)
        if not ok:
            print("  measured: plan=%r bytes=%r verdict=%r counts=%r"
                  % (same_plan, same_bytes, same_verdict, counts), flush=True)
        check(ok, "AC-GDRTW4 success path byte-identical to the direct plan")
    finally:
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(twin, ignore_errors=True)


def ac_gdrtw5():
    """CLI codes 0/2/3/5 and one byte-stable pinned JSON."""
    world = make_world(tech=WORLD_ROWS,
                       decl=declaration([MISSING_ID, OPEN_ID]))
    nodecl = make_world(tech=WORLD_ROWS, decl=declaration([MISSING_ID]))
    try:
        os.remove(decl_path(nodecl))
        rc_plan, _ = run_cli(world, ["--identity", MISSING_ID])
        rc_refuse, _ = run_cli(world, ["--identity", OPEN_ID])
        rc_nodecl, _ = run_cli(nodecl, ["--identity", MISSING_ID])
        rc_flags, _ = run_cli(world, ["--identity"])
        json_a, body_a = run_cli(world, ["--identity", MISSING_ID, "--json"])
        json_b, body_b = run_cli(world, ["--identity", MISSING_ID, "--json"])
        parsed = json.loads(body_a)
        ok = (rc_plan == 0 and rc_refuse == 2 and rc_nodecl == 3
              and rc_flags == 5 and json_a == 0 and json_b == 0
              and body_a == body_b
              and tuple(parsed.keys()) == GDRTW.REPORT_KEYS
              and parsed["verdict"] == GDRTW.VERDICT_PLANNED
              and parsed["state"] == "UNMATCHED")
        if not ok:
            print("  measured: rc=%r/%r/%r/%r json=%r keys=%r"
                  % (rc_plan, rc_refuse, rc_nodecl, rc_flags, json_a,
                     tuple(parsed.keys())), flush=True)
        check(ok, "AC-GDRTW5 CLI codes and a byte-stable pinned JSON")
    finally:
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(nodecl, ignore_errors=True)


def ac_gdrtw6():
    """Pure ASCII, no network, no clock, and wired in the runner."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = not re.search(r"\b(?:socket|urllib|http)\b", source)
    no_clock = not re.search(r"\b(?:import time|import datetime|time\.time)\b",
                             source)
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner
             and "test_gate_decl_retire_wire.py" in runner)
    world = make_world(tech=WORLD_ROWS, decl=declaration([MISSING_ID]))
    try:
        before = tree_digest(world)
        GDRTW.plan(world, MISSING_ID)
        after = tree_digest(world)
        ok = ascii_only and no_net and no_clock and wired and before == after
        if not ok:
            print("  measured: ascii=%r net=%r clock=%r wired=%r writes=%r"
                  % (ascii_only, no_net, no_clock, wired, before == after),
                  flush=True)
        check(ok, "AC-GDRTW6 pure, wired, and writes nothing")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def main():
    print("gate_decl_retire_wire suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_gdrtw1()
    ac_gdrtw2()
    ac_gdrtw3()
    ac_gdrtw4()
    ac_gdrtw5()
    ac_gdrtw6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())