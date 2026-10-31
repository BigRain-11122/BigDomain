"""gate_decl_identity_wire suite (R2315; criteria AC-GDIW1..AC-GDIW6 were
pre-registered inside the R2314 seed row of state/queue/tech.md BEFORE this
code existed).

What this proves: the declaration writer no longer owns a permissive address
rule of its own. The identity is resolved through gate_decl_identity's rows
and resolve imports, only a MATCHED identity reaches gate_decl_append.plan,
and UNMATCHED / AMBIGUOUS are refused before any byte changes with the reader
state and its carrier lines in the detail. The suite proves the import by
patching the reader and watching the refusal move, and proves there is no
second address scan by patching rows to an empty reading.

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

import gate_decl_append as GDA  # noqa: E402
import gate_decl_identity as GDI  # noqa: E402
import gate_decl_identity_wire as GDIW  # noqa: E402
import machine_gate as MG  # noqa: E402
import queue_row as QR  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "gate_decl_identity_wire.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-gate-decl-identity-wire"

HEADER = "# queue test world\n\nprose that never becomes a row\n\n"
ROW_GATED = "- [ ] docker sandbox row, blocked on CEO merchant number: AC-GAT1 pinned"
ROW_DONE = "- [x] [done 2026-11-01 R2300] closed row: AC-DON1 pinned"
ROW_OPEN = "- [ ] open product row: Criteria prefix AC-OPE1 pinned here"
ROW_DUP = "- [ ] duplicated row: AC-DUP1 pinned here"

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


def declaration(identities):
    """A declaration body carrying one entry per identity."""
    gates = [{"identity": identity,
              "capability": "docker",
              "reason": "suite declaration",
              "declared_by": "R2315"} for identity in identities]
    return {"version": 1,
            "declared_by": "R2315",
            "reason": "suite declaration",
            "gates": gates}


def make_world(tech=None, decl=None, write_decl=True):
    """Build a temp root with the three queue files and one declaration."""
    world = tempfile.mkdtemp(prefix="bigdomain-gdiw-")
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
DUP_ID = identity_of_row(ROW_DUP)
MISSING_ID = "AC-NONE1#deadbeef"


def refusal(func, *args, **kwargs):
    """Run one call and return (code, detail) or (None, None)."""
    try:
        func(*args, **kwargs)
    except GDIW.WireError as exc:
        return exc.code, exc.detail
    return None, None


def ac_gdiw1():
    """The resolution is imported: patching the reader moves the refusal."""
    world = make_world(tech=WORLD_ROWS, decl=declaration([]))
    try:
        code, _detail = refusal(GDIW.plan, world, MISSING_ID, "docker",
                                "suite", "R2315")
        refused = code == "E_GDIW_UNMATCHED"

        original_resolve = GDI.resolve
        GDI.resolve = lambda identity, rows_found: {
            "state": "MATCHED", "line": 9, "prefix": None, "level": "open",
            "claimable": True, "detail": "patched reader", "carriers": []}
        try:
            report = GDIW.plan(world, MISSING_ID, "docker", "suite", "R2315")
            moved = report["verdict"] == GDIW.VERDICT_PLANNED
        finally:
            GDI.resolve = original_resolve

        original_rows = GDI.rows
        GDI.rows = lambda root, name="tech": []
        try:
            code_rows, _ = refusal(GDIW.plan, world, OPEN_ID, "docker",
                                   "suite", "R2315")
            rows_moved = code_rows == "E_GDIW_UNMATCHED"
        finally:
            GDI.rows = original_rows

        source = io.open(MODULE, "r", encoding="utf-8").read()
        no_second_scan = (
            not re.search(r"^\s*(?:import|from)\s+queue_head", source, re.M)
            and not re.search(r"open\([^)\n]*queue", source)
            and "import gate_decl_identity as GDI" in source)
        ok = refused and moved and rows_moved and no_second_scan
        if not ok:
            print("  measured: refused=%r moved=%r rows_moved=%r scan=%r"
                  % (refused, moved, rows_moved, no_second_scan), flush=True)
        check(ok, "AC-GDIW1 the resolution is the reader's, not a second scan")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_gdiw2():
    """UNMATCHED and AMBIGUOUS refuse before any byte, MATCHED dup as before."""
    world = make_world(tech=WORLD_ROWS, decl=declaration([OPEN_ID]))
    try:
        before = decl_bytes(world)

        code_un, detail_un = refusal(GDIW.plan, world, MISSING_ID, "docker",
                                     "suite", "R2315")
        unmatched_ok = (code_un == "E_GDIW_UNMATCHED"
                        and "UNMATCHED" in detail_un
                        and "carriers none" in detail_un)

        code_am, detail_am = refusal(GDIW.plan, world, DUP_ID, "docker",
                                     "suite", "R2315")
        ambiguous_ok = (code_am == "E_GDIW_AMBIGUOUS"
                        and "AMBIGUOUS" in detail_am
                        and "L8" in detail_am and "L9" in detail_am)
        if not ambiguous_ok:
            print("  measured: ambiguous code=%r detail=%r"
                  % (code_am, detail_am), flush=True)

        code_dup, detail_dup = refusal(GDIW.plan, world, OPEN_ID, "docker",
                                       "suite", "R2315")
        dup_ok = (code_dup == "E_GDA_DUP" and OPEN_ID in detail_dup)

        after = decl_bytes(world)
        ok = unmatched_ok and ambiguous_ok and dup_ok and before == after
        if not ok:
            print("  measured: un=%r/%r am=%r dup=%r same=%r"
                  % (unmatched_ok, detail_un, ambiguous_ok, dup_ok,
                     before == after), flush=True)
        check(ok, "AC-GDIW2 UNMATCHED/AMBIGUOUS refused before any byte")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_gdiw3():
    """The dry run reports the reader state and writes nothing."""
    world = make_world(tech=WORLD_ROWS, decl=declaration([]))
    try:
        before_digest = tree_digest(world)
        report = GDIW.plan(world, OPEN_ID, "docker", "suite", "R2315")
        after_digest = tree_digest(world)
        dry_ok = (report["state"] == "MATCHED"
                  and report["verdict"] == GDIW.VERDICT_PLANNED
                  and report["wrote"] is False
                  and before_digest == after_digest)
        refusal_code, _ = refusal(GDIW.plan, world, MISSING_ID, "docker",
                                  "suite", "R2315")
        refused_digest = tree_digest(world)
        ok = (dry_ok and refusal_code == "E_GDIW_UNMATCHED"
              and refused_digest == before_digest)
        if not ok:
            print("  measured: dry=%r refusal=%r writes=%r"
                  % (dry_ok, refusal_code, refused_digest == before_digest),
                  flush=True)
        check(ok, "AC-GDIW3 dry run names the state and writes nothing")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_gdiw4():
    """The positive path appends one entry and keeps the rest byte-intact."""
    world = make_world(tech=WORLD_ROWS, decl=declaration([identity_of_row(ROW_GATED)]))
    try:
        with io.open(decl_path(world), "r", encoding="utf-8") as handle:
            kept = handle.read().split("\n")[7]
        report = GDIW.plan(world, OPEN_ID, "docker", "suite", "R2315",
                           execute=True)
        with io.open(decl_path(world), "r", encoding="utf-8") as handle:
            text = handle.read()
        parsed = MG.read_declaration_text(text)
        added = [row for row in parsed["gates"] if row["identity"] == OPEN_ID]
        ok = (report["verdict"] == GDIW.VERDICT_APPENDED
              and report["wrote"] is True
              and report["read_back_ok"] is True
              and len(parsed["gates"]) == 2
              and len(added) == 1
              and cut_ok(text, kept))
        if not ok:
            print("  measured: verdict=%r wrote=%r entries=%d added=%d"
                  % (report["verdict"], report["wrote"],
                     len(parsed["gates"]), len(added)), flush=True)
        check(ok, "AC-GDIW4 one entry appended, the survivor byte-intact")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def cut_ok(text, kept):
    """The pre-existing entry's own line survives verbatim."""
    return bool(kept) and kept in text


def ac_gdiw5():
    """CLI codes 0/2/3/5 and one byte-stable pinned JSON."""
    world = make_world(tech=WORLD_ROWS, decl=declaration([]))
    nodecl = make_world(tech=WORLD_ROWS, decl=declaration([]))
    try:
        os.remove(decl_path(nodecl))
        base_args = ["--identity", OPEN_ID, "--capability", "docker",
                     "--reason", "suite", "--declared-by", "R2315"]
        rc_plan, _ = run_cli(world, base_args)
        rc_unmatched, _ = run_cli(world, ["--identity", MISSING_ID,
                                          "--capability", "docker",
                                          "--reason", "suite",
                                          "--declared-by", "R2315"])
        rc_nodecl, _ = run_cli(nodecl, base_args)
        rc_flags, _ = run_cli(world, ["--identity", OPEN_ID])
        json_a, body_a = run_cli(world, base_args + ["--json"])
        json_b, body_b = run_cli(world, base_args + ["--json"])
        parsed = json.loads(body_a)
        ok = (rc_plan == 0 and rc_unmatched == 2 and rc_nodecl == 3
              and rc_flags == 5 and json_a == 0 and json_b == 0
              and body_a == body_b
              and tuple(parsed.keys()) == GDIW.REPORT_KEYS
              and parsed["verdict"] == GDIW.VERDICT_PLANNED)
        if not ok:
            print("  measured: rc=%r/%r/%r/%r json=%r keys=%r"
                  % (rc_plan, rc_unmatched, rc_nodecl, rc_flags, json_a,
                     tuple(parsed.keys())), flush=True)
        check(ok, "AC-GDIW5 CLI codes and a byte-stable pinned JSON")
    finally:
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(nodecl, ignore_errors=True)


def ac_gdiw6():
    """Pure ASCII, no network, no clock, and wired in the runner."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = not re.search(r"\b(?:socket|urllib|http)\b", source)
    no_clock = not re.search(r"\b(?:import time|import datetime|time\.time)\b",
                             source)
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner
             and "test_gate_decl_identity_wire.py" in runner)
    world = make_world(tech=WORLD_ROWS, decl=declaration([]))
    try:
        before = tree_digest(world)
        GDIW.plan(world, OPEN_ID, "docker", "suite", "R2315")
        after = tree_digest(world)
        ok = ascii_only and no_net and no_clock and wired and before == after
        if not ok:
            print("  measured: ascii=%r net=%r clock=%r wired=%r writes=%r"
                  % (ascii_only, no_net, no_clock, wired, before == after),
                  flush=True)
        check(ok, "AC-GDIW6 pure, wired, and writes nothing")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def main():
    print("gate_decl_identity_wire suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_gdiw1()
    ac_gdiw2()
    ac_gdiw3()
    ac_gdiw4()
    ac_gdiw5()
    ac_gdiw6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())