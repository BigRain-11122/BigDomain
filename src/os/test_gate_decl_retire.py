"""gate_decl_retire suite (R2317; criteria AC-GDRT1..AC-GDRT6 were
pre-registered inside the R2312 seed row of state/queue/tech.md BEFORE this
code existed).

What this proves: a capability blocker can finally be retired, and only when
it has stopped doing its job. The entry keys, the declaration keys and the
post read-back are imported from machine_gate, the live "does this entry
still block a row" reading is machine_gate.gate itself, and the array span
comes from gate_decl_append - the suite patches each law and watches the
verdict move. An undeclared identity and a still-blocking entry are refused
before any byte changes; the write is one atomic replace with a read-back
byte proof and no temp residue; every surviving entry stays byte-intact.

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
sys.path.insert(0, BASE)

import gate_decl_append as GDA  # noqa: E402
import gate_decl_retire as GDRT  # noqa: E402
import machine_gate as MG  # noqa: E402
import queue_row as QR  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "gate_decl_retire.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-gate-decl-retire"

HEADER = "# queue test world\n\nprose that never becomes a row\n\n"
ROW_A = "- [ ] open product row alpha: Criteria prefix AC-RETA1 pinned here"
ROW_B = "- [ ] open product row beta: Criteria prefix AC-RETB1 pinned here"
WORLD_ROWS = HEADER + ROW_A + "\n" + ROW_B + "\n"

GHOST = "AC-GHST1#deadbeef"
SECOND = "AC-GHST2#deadbeef"

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
    """The identity a row carries, read through machine_gate's own law."""
    return MG.identity_of(QR.scan_row(line)["prefix"], line)


def declaration(identities):
    """A declaration body carrying one entry per identity."""
    gates = [{"identity": identity,
              "capability": "docker",
              "reason": "suite declaration %d" % index,
              "declared_by": "R2317"} for index, identity in enumerate(identities)]
    return {"version": 1,
            "declared_by": "R2317",
            "reason": "suite declaration",
            "gates": gates}


def make_world(tech=None, decl=None, raw_decl=None, write_decl=True):
    """Build a temp root with the three queue files and one declaration."""
    world = tempfile.mkdtemp(prefix="bigdomain-gdrt-")
    queue = os.path.join(world, "state", "queue")
    os.makedirs(queue)
    bodies = {"tech": tech if tech is not None else WORLD_ROWS,
              "main": HEADER, "explore": HEADER}
    for name, body in bodies.items():
        with io.open(os.path.join(queue, "%s.md" % name), "w",
                     encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    if write_decl:
        path = os.path.join(world, MG.DEFAULT_DECLARATION)
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            if raw_decl is not None:
                handle.write(raw_decl)
            else:
                handle.write(json.dumps(decl if decl is not None
                                        else declaration([GHOST]), indent=2))
    return world


def decl_text(world):
    """The declaration bytes as text."""
    with io.open(os.path.join(world, MG.DEFAULT_DECLARATION), "r",
                 encoding="utf-8") as handle:
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


def ac_gdrt1():
    """Keys, post reader and the live block reading are imported laws."""
    world = make_world(decl=declaration([GHOST]))
    original_text = MG.read_declaration_text
    original_gate = MG.gate
    try:
        text = decl_text(world)
        live = MG.gate(world, "tech")
        baseline = GDRT.plan(text, GHOST, live)

        def refuse(_text, _where="<text>"):
            raise MG.MachineGateError("E_MGT_BAD_DECL", "patched reader")

        MG.read_declaration_text = refuse
        refused = None
        try:
            GDRT.plan(text, GHOST, live)
        except GDRT.GateDeclRetireError as exc:
            refused = exc.code
        MG.read_declaration_text = original_text

        MG.gate = lambda _root, _name="tech", _decl=None: {
            "blocked": [{"identity": GHOST, "line": 99}], "inert": []}
        blocked = None
        try:
            GDRT.retire(world, GHOST)
        except GDRT.GateDeclRetireError as exc:
            blocked = exc.code
        MG.gate = original_gate

        source = io.open(MODULE, "r", encoding="utf-8").read()
        no_own_keys = "ENTRY_KEYS" not in source and "DECLARATION_KEYS" not in source
        no_own_array = "def array_span" in source and "GDA.array_span" in source
        ok = (baseline["removed_at"] == 0
              and refused == "E_GDRT_BAD_DECL"
              and blocked == "E_GDRT_STILL_BLOCKED"
              and no_own_keys and no_own_array)
        if not ok:
            print("  measured: removed=%r refused=%r blocked=%r ownkeys=%r "
                  "array=%r" % (baseline["removed_at"], refused, blocked,
                                no_own_keys, no_own_array), flush=True)
        check(ok, "AC-GDRT1 shape, post reader and live block are imported")
    finally:
        MG.read_declaration_text = original_text
        MG.gate = original_gate
        shutil.rmtree(world, ignore_errors=True)


def ac_gdrt2():
    """An undeclared identity and a still-blocking entry are refused first."""
    rows = [identity_of_row(ROW_A), identity_of_row(ROW_B)]
    world = make_world(decl=declaration(rows))
    try:
        before = tree_digest(world)
        undeclared = None
        try:
            GDRT.retire(world, GHOST)
        except GDRT.GateDeclRetireError as exc:
            undeclared = exc
        blocked = None
        try:
            GDRT.retire(world, rows[0])
        except GDRT.GateDeclRetireError as exc:
            blocked = exc
        after = tree_digest(world)
        line = WORLD_ROWS.split("\n").index(ROW_A) + 1
        ok = (undeclared is not None
              and undeclared.code == "E_GDRT_UNDECLARED"
              and "field identity" in undeclared.detail
              and GHOST in undeclared.detail
              and blocked is not None
              and blocked.code == "E_GDRT_STILL_BLOCKED"
              and "field identity" in blocked.detail
              and rows[0] in blocked.detail
              and ("line %d" % line) in blocked.detail
              and before == after)
        if not ok:
            print("  measured: undeclared=%r blocked=%r writes=%r"
                  % (undeclared and undeclared.code,
                     blocked and blocked.code, before == after), flush=True)
        check(ok, "AC-GDRT2 both refusals name the field and write nothing")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_gdrt3():
    """The plan writes nothing; execute writes exactly the prediction."""
    world = make_world(decl=declaration([GHOST, SECOND]))
    try:
        text = decl_text(world)
        before_digest = tree_digest(world)
        planned = GDRT.retire(world, SECOND)
        after_plan_digest = tree_digest(world)
        done = GDRT.retire(world, SECOND, execute=True)
        with io.open(os.path.join(world, MG.DEFAULT_DECLARATION), "rb") as fh:
            on_disk = fh.read()
        temp_left = os.path.exists(
            os.path.join(world, MG.DEFAULT_DECLARATION) + GDRT.TEMP_SUFFIX)
        ok = (planned["verdict"] == "PLANNED"
              and planned["wrote"] is False
              and planned["removed_at"] == 1
              and planned["before_bytes"] == len(text.encode("utf-8"))
              and planned["predicted_bytes"] < planned["before_bytes"]
              and before_digest == after_plan_digest
              and done["verdict"] == "RETIRED"
              and done["wrote"] is True
              and done["read_back_ok"] is True
              and len(on_disk) == done["predicted_bytes"]
              and not temp_left)
        if not ok:
            print("  measured: plan=%r exec=%r bytes=%r/%r temp=%r"
                  % (planned["verdict"], done["verdict"], len(on_disk),
                     done["predicted_bytes"], temp_left), flush=True)
        check(ok, "AC-GDRT3 dry run writes nothing, execute is exact")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_gdrt4():
    """The post re-parses with one fewer entry and survivors stay intact."""
    world = make_world(decl=declaration([GHOST, SECOND, "-"]))
    try:
        text = decl_text(world)
        open_at, close_at = GDA.array_span(text, "gates")
        body = text[open_at + 1:close_at]
        spans = GDRT.entry_spans(body)
        survivors = [body[start:end] for index, (start, end) in enumerate(spans)
                     if index != 1]
        report = GDRT.retire(world, SECOND, execute=True)
        post = decl_text(world)
        parsed = MG.read_declaration_text(post)
        post_open, post_close = GDA.array_span(post, "gates")
        post_body = post[post_open + 1:post_close]
        ok = (len(spans) == 3
              and report["declarations_before"] == 3
              and report["declarations_after"] == 2
              and len(parsed["gates"]) == 2
              and all(row["identity"] != SECOND for row in parsed["gates"])
              and all(survivor in post_body for survivor in survivors)
              and parsed["declared_by"] == "R2317"
              and parsed["version"] == 1)
        if not ok:
            print("  measured: spans=%d before=%r after=%r alive=%r"
                  % (len(spans), report["declarations_before"],
                     report["declarations_after"],
                     [row["identity"] for row in parsed["gates"]]), flush=True)
        check(ok, "AC-GDRT4 post carries one fewer entry, survivors intact")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_gdrt5():
    """CLI exits 0 / 2 / 3 / 5 with a byte-stable pinned --json."""
    good = make_world(decl=declaration([GHOST, SECOND]))
    legacy = make_world(decl=declaration([identity_of_row(ROW_A)]))
    nodecl = make_world(write_decl=False)
    try:
        rc_plan, _out = run_cli(good, ["--identity", SECOND])
        rc_block, _out = run_cli(legacy, ["--identity", identity_of_row(ROW_A)])
        rc_nodecl, _out = run_cli(nodecl, ["--identity", SECOND])
        rc_flag, _out = run_cli(good, ["--identity", SECOND, "--bogus"])
        rc_json_a, body_a = run_cli(good, ["--identity", SECOND, "--json"])
        rc_json_b, body_b = run_cli(good, ["--identity", SECOND, "--json"])
        parsed = json.loads(body_a)
        ok = (rc_plan == 0 and rc_block == 2 and rc_nodecl == 3
              and rc_flag == 5 and rc_json_a == 0 and rc_json_b == 0
              and body_a == body_b
              and tuple(parsed.keys()) == GDRT.REPORT_KEYS
              and parsed["verdict"] == "PLANNED"
              and parsed["identity"] == SECOND)
        if not ok:
            print("  measured: rc=%r/%r/%r/%r keys=%r"
                  % (rc_plan, rc_block, rc_nodecl, rc_flag,
                     tuple(parsed.keys())), flush=True)
        check(ok, "AC-GDRT5 CLI codes and a byte-stable pinned JSON")
    finally:
        for world in (good, legacy, nodecl):
            shutil.rmtree(world, ignore_errors=True)


def ac_gdrt6():
    """Pure ASCII, no network, no clock, wired, and a plan writes nothing."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = not re.search(r"\b(?:socket|urllib|http)\b", source)
    no_clock = not re.search(r"\b(?:import time|import datetime|time\.time)\b",
                             source)
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = '"%s"' % LABEL in runner and "test_gate_decl_retire.py" in runner
    world = make_world(decl=declaration([GHOST]))
    try:
        before = tree_digest(world)
        report = GDRT.retire(world, GHOST)
        after = tree_digest(world)
        ok = (ascii_only and no_net and no_clock and wired
              and before == after and report["verdict"] == "PLANNED")
        if not ok:
            print("  measured: ascii=%r net=%r clock=%r wired=%r writes=%r"
                  % (ascii_only, no_net, no_clock, wired, before == after),
                  flush=True)
        check(ok, "AC-GDRT6 pure, wired, and a plan writes nothing")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def main():
    print("gate_decl_retire suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_gdrt1()
    ac_gdrt2()
    ac_gdrt3()
    ac_gdrt4()
    ac_gdrt5()
    ac_gdrt6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())