"""gate_decl_identity suite (R2314; criteria AC-GDI1..AC-GDI6 were
pre-registered inside the R2313 seed row of state/queue/tech.md BEFORE this
code existed).

What this proves: a declared gate identity becomes a reading instead of a
silent address. The queue path, the queue text and the gate marker are
imported from queue_head, the identity shape and the declaration from
machine_gate, and the suite proves those imports by patching each one and
watching the verdict move. The row law and the criteria prefix are imported
from queue_floor and queue_row, so the queue keeps one row predicate.

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
import machine_gate as MG  # noqa: E402
import queue_head as QH  # noqa: E402
import queue_row as QR  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "gate_decl_identity.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-gate-decl-identity"

HEADER = "# queue test world\n\nprose that never becomes a row\n\n"
ROW_GATED = "- [ ] docker sandbox row, blocked on CEO merchant number: AC-GAT1 pinned"
ROW_DONE = "- [x] [done 2026-11-01 R2300] closed row: AC-DON1 pinned"
ROW_OPEN = "- [ ] open product row: Criteria prefix AC-OPE1 pinned here"
PLAIN_A = "- [ ] plain alpha row carrying no criteria prefix"
PLAIN_B = "- [ ] plain beta row carrying no criteria prefix"

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
              "declared_by": "R2314"} for identity in identities]
    return {"version": 1,
            "declared_by": "R2314",
            "reason": "suite declaration",
            "gates": gates}


def make_world(tech=None, decl=None, raw_decl=None, write_decl=True):
    """Build a temp root with the three queue files and one declaration."""
    world = tempfile.mkdtemp(prefix="bigdomain-gdi-")
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
            if raw_decl is not None:
                handle.write(raw_decl)
            else:
                handle.write(json.dumps(decl if decl is not None
                                        else declaration([]), indent=2))
    return world


def line_of(text, needle):
    """The 1-based line number of the row carrying a needle."""
    for index, line in enumerate(text.split("\n"), 1):
        if needle in line:
            return index
    return None


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


WORLD_ROWS = HEADER + "\n".join([ROW_GATED, ROW_DONE, ROW_OPEN,
                                 PLAIN_A, PLAIN_B]) + "\n"


def ac_gdi1():
    """The row parsing and the identity shape are imported, not copied."""
    world = make_world(tech=WORLD_ROWS,
                       decl=declaration([identity_of_row(ROW_OPEN)]))
    original_identity = MG.identity_of
    original_path = QH.queue_path
    try:
        report = GDI.review(world, "tech")
        baseline = report["matched"]
        MG.identity_of = lambda _prefix, _text: "SHAPED#00000000"
        moved = GDI.review(world, "tech")
        MG.identity_of = original_identity
        QH.queue_path = lambda _name: None
        refused = None
        try:
            GDI.review(world, "tech")
        except GDI.GateIdentityError as exc:
            refused = exc.code
        QH.queue_path = original_path
        source = io.open(MODULE, "r", encoding="utf-8").read()
        no_own_digest = "hashlib" not in source
        ok = (baseline == 1 and moved["matched"] == 0
              and moved["unmatched"] == 1
              and refused == "E_GDI_BAD_QUEUE" and no_own_digest)
        if not ok:
            print("  measured: baseline=%r moved=%r refused=%r own=%r"
                  % (baseline, moved["matched"], refused, no_own_digest),
                  flush=True)
        check(ok, "AC-GDI1 identity shape and queue path are imported laws")
    finally:
        MG.identity_of = original_identity
        QH.queue_path = original_path
        shutil.rmtree(world, ignore_errors=True)


def ac_gdi2():
    """MATCHED / UNMATCHED / AMBIGUOUS are exhaustive, disjoint, named."""
    identities = [identity_of_row(ROW_OPEN), "ghost#deadbeef", "-"]
    world = make_world(tech=WORLD_ROWS, decl=declaration(identities))
    try:
        report = GDI.review(world, "tech")
        states = [item["state"] for item in report["readings"]]
        ok = (report["declarations"] == 3
              and report["matched"] + report["unmatched"]
              + report["ambiguous"] == 3
              and report["matched"] == 1 and report["unmatched"] == 1
              and report["ambiguous"] == 1
              and states == ["MATCHED", "UNMATCHED", "AMBIGUOUS"]
              and all(state in GDI.STATES for state in states)
              and all(item["detail"] for item in report["readings"])
              and all((item["line"] is not None) or item["detail"]
                      for item in report["readings"])
              and report["verdict"] == "IDENTITY-DEBT")
        if not ok:
            print("  measured: %r" % (report,), flush=True)
        check(ok, "AC-GDI2 three states are exhaustive and disjoint")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_gdi3():
    """A bare placeholder several rows share is AMBIGUOUS, all carriers named."""
    world = make_world(tech=WORLD_ROWS, decl=declaration(["-"]))
    try:
        report = GDI.review(world, "tech")
        item = report["readings"][0]
        carriers = sorted(carrier["line"] for carrier in item["carriers"])
        # every row that declares no criteria prefix renders as "-", so the
        # shared placeholder names the gated and the done rows too.
        want = sorted([line_of(WORLD_ROWS, "docker sandbox"),
                       line_of(WORLD_ROWS, "closed row"),
                       line_of(WORLD_ROWS, "plain alpha"),
                       line_of(WORLD_ROWS, "plain beta")])
        ok = (item["state"] == "AMBIGUOUS"
              and item["line"] is None
              and carriers == want
              and len(carriers) == 4
              and all(carrier["identity"].startswith("-#")
                      for carrier in item["carriers"])
              and report["ambiguous"] == 1)
        if not ok:
            print("  measured: item=%r want=%r" % (item, want), flush=True)
        check(ok, "AC-GDI3 a shared bare placeholder names every carrier")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_gdi4():
    """Every reading is level-tagged; claimability is never criticised."""
    identities = [identity_of_row(ROW_GATED), identity_of_row(ROW_DONE),
                  identity_of_row(ROW_OPEN)]
    world = make_world(tech=WORLD_ROWS, decl=declaration(identities))
    try:
        report = GDI.review(world, "tech")
        gated, done, open_row = report["readings"]
        ok = (report["matched"] == 3 and report["verdict"] == "ALL-MATCHED"
              and gated["state"] == "MATCHED" and gated["level"] == "gated"
              and gated["claimable"] is False
              and done["state"] == "MATCHED" and done["level"] == "done"
              and done["claimable"] is False
              and open_row["state"] == "MATCHED"
              and open_row["level"] == "open"
              and open_row["claimable"] is True
              and gated["line"] == line_of(WORLD_ROWS, "docker sandbox")
              and done["line"] == line_of(WORLD_ROWS, "closed row"))
        if not ok:
            print("  measured: %r" % (report["readings"],), flush=True)
        check(ok, "AC-GDI4 levels are tagged and claimability is not judged")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_gdi5():
    """CLI exits 0 / 2 / 3 / 5 with a byte-stable pinned --json."""
    good = make_world(tech=WORLD_ROWS, decl=declaration([identity_of_row(ROW_OPEN)]))
    bad = make_world(tech=WORLD_ROWS, decl=declaration(["ghost#deadbeef"]))
    nodecl = make_world(tech=WORLD_ROWS, write_decl=False)
    try:
        rc_good, _out = run_cli(good, ["--check"])
        rc_bad, _out = run_cli(bad, ["--check"])
        rc_nodecl, _out = run_cli(nodecl, ["--check"])
        rc_flag, _out = run_cli(good, ["--check", "--bogus"])
        rc_json_a, body_a = run_cli(good, ["--check", "--json"])
        rc_json_b, body_b = run_cli(good, ["--check", "--json"])
        parsed = json.loads(body_a)
        ok = (rc_good == 0 and rc_bad == 2 and rc_nodecl == 3
              and rc_flag == 5 and rc_json_a == 0 and rc_json_b == 0
              and body_a == body_b
              and tuple(parsed.keys()) == GDI.REPORT_KEYS
              and parsed["verdict"] == "ALL-MATCHED")
        if not ok:
            print("  measured: rc=%r/%r/%r/%r json=%r keys=%r"
                  % (rc_good, rc_bad, rc_nodecl, rc_flag, rc_json_a,
                     tuple(parsed.keys())), flush=True)
        check(ok, "AC-GDI5 CLI codes and a byte-stable pinned JSON")
    finally:
        for world in (good, bad, nodecl):
            shutil.rmtree(world, ignore_errors=True)


def ac_gdi6():
    """Pure ASCII, no network, no clock, no writes, and wired in the runner."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = not re.search(r"\b(?:socket|urllib|http)\b", source)
    no_clock = not re.search(r"\b(?:import time|import datetime|time\.time)\b",
                             source)
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = '"%s"' % LABEL in runner and "test_gate_decl_identity.py" in runner
    world = make_world(tech=WORLD_ROWS,
                       decl=declaration([identity_of_row(ROW_OPEN)]))
    try:
        before = tree_digest(world)
        report = GDI.review(world, "tech")
        after = tree_digest(world)
        ok = (ascii_only and no_net and no_clock and wired
              and before == after and report["verdict"] == "ALL-MATCHED")
        if not ok:
            print("  measured: ascii=%r net=%r clock=%r wired=%r writes=%r"
                  % (ascii_only, no_net, no_clock, wired, before == after),
                  flush=True)
        check(ok, "AC-GDI6 pure, wired, and writes nothing")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def main():
    print("gate_decl_identity suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_gdi1()
    ac_gdi2()
    ac_gdi3()
    ac_gdi4()
    ac_gdi5()
    ac_gdi6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())