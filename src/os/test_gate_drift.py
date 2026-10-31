"""gate_drift suite (R2300; criteria AC-GDR1..AC-GDR6 were pre-registered
inside the R2286 seed row of state/queue/tech.md BEFORE this code existed).

What this proves: an inert machine gate becomes a decision instead of a
shrug. The gate reading and the declaration are imported from machine_gate -
the inert list is never re-derived - and the suite proves the import by
patching that reading and watching the split follow. The row and prefix laws
are imported from queue_floor and queue_row, so the queue keeps one row
predicate.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

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

import gate_drift as GD  # noqa: E402
import machine_gate as MG  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "gate_drift.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-gate-drift"

HEADER = "# queue test world\n\nprose that never becomes a row\n\n"
ROW_A = "- [ ] alpha row: Criteria prefix AC-AAA1 pinned here first\n"
ROW_B = "- [ ] beta row: Criteria prefix AC-BBB1 pinned here first\n"
ROW_A_EDIT = "- [ ] alpha row: Criteria prefix AC-AAA1 pinned here, rewritten\n"
PLAIN = "- [ ] a row carrying no criteria prefix at all\n"

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


def declaration(entries):
    """A declaration body built from (identity, capability, reason) legs."""
    gates = []
    for identity, capability, reason in entries:
        gates.append({"identity": identity,
                      "capability": capability,
                      "reason": reason,
                      "declared_by": "R2300"})
    return {"version": 1,
            "declared_by": "R2300",
            "reason": "suite declaration",
            "gates": gates}


def make_world(tech, decl=None, raw_decl=None):
    """Build a temp root with the three queue files and one declaration."""
    world = tempfile.mkdtemp(prefix="bigdomain-gdr-")
    queue = os.path.join(world, "state", "queue")
    os.makedirs(queue)
    bodies = {"tech": tech, "main": HEADER, "explore": HEADER}
    for name, body in bodies.items():
        with io.open(os.path.join(queue, "%s.md" % name), "w",
                     encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    if raw_decl is not None:
        with io.open(os.path.join(world, "state", "machine_gates.json"), "w",
                     encoding="utf-8", newline="\n") as handle:
            handle.write(raw_decl)
    elif decl is not None:
        with io.open(os.path.join(world, "state", "machine_gates.json"), "w",
                     encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(decl, ensure_ascii=True, indent=2))
    return world


def tree_digest(world):
    """Every file under the world with its size, in walk order."""
    out = []
    for root, dirs, files in os.walk(world):
        dirs.sort()
        for name in sorted(files):
            path = os.path.join(root, name)
            rel = os.path.relpath(path, world)
            out.append("%s:%d" % (rel, os.path.getsize(path)))
    return "|".join(out)


def identity_of(prefix, body):
    return MG.identity_of(prefix, body.rstrip("\n"))


def run_cli(world, extra=()):
    argv = [sys.executable, MODULE, "--drift", "tech", "--root", world]
    argv.extend(extra)
    proc = subprocess.run(argv, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def ac_gdr1():
    """AC-GDR1: the gate reading is imported and a patched reading flows."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    imported = "MG.gate(" in source
    no_decl_reader = ("def read_declaration" not in source
                      and "machine_gates.json" not in source)
    no_row_law = ("def is_open_row" not in source
                  and "def is_done_row" not in source
                  and 'startswith("- [' not in source)
    # A declaration only reads INERT when it matches no CLAIMABLE candidate,
    # so the live leg keys the edited row's old identity: the row is still in
    # the queue, its text no longer matches, and the gate calls it inert.
    tech = HEADER + ROW_A_EDIT + ROW_B
    edited = identity_of("AC-AAA1", ROW_A)
    world = make_world(tech, declaration([(edited, "docker", "no docker")]))
    try:
        live = GD.review(world, "tech")
        saved = MG.gate

        def patched(root, name="tech", declaration=None):
            return {"queue": name, "path": "state/queue/tech.md",
                    "declaration": "state/machine_gates.json",
                    "declarations": 1, "candidates": 0, "offered": None,
                    "blocked": [], "blocked_rows": 0,
                    "inert": [{"identity": "AC-PATCH#deadbeef",
                               "capability": "docker", "reason": "r",
                               "declared_by": "R2300", "line": None}]}
        try:
            MG.gate = patched
            forced = GD.review(world, "tech")
        finally:
            MG.gate = saved
        ok = (imported and no_decl_reader and no_row_law
              and live["inert"] == 1
              and live["drift"][0]["prefix"] == "AC-AAA1"
              and forced["drift_count"] + forced["gone_count"] == 1
              and forced["gone"][0]["prefix"] == "AC-PATCH")
        if not ok:
            print("  measured: imported=%r no_decl=%r no_row_law=%r "
                  "live=%r forced=%r"
                  % (imported, no_decl_reader, no_row_law, live, forced),
                  flush=True)
        check(ok, "AC-GDR1 gate reading imported, a patched reading flows")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_gdr2():
    """AC-GDR2: DRIFT names both identities, the line and the prefix; GONE
    names the prefix with no line."""
    old = identity_of("AC-AAA1", ROW_A)
    moved_world = make_world(HEADER + ROW_A_EDIT + ROW_B,
                             declaration([(old, "docker", "no docker")]))
    gone_world = make_world(HEADER + ROW_B,
                            declaration([(old, "docker", "no docker")]))
    try:
        moved = GD.review(moved_world, "tech")
        gone = GD.review(gone_world, "tech")
        item = moved["drift"][0]
        fired = gone["gone"][0]
        ok = (item["prefix"] == "AC-AAA1"
              and item["old_identity"] == old
              and item["new_identity"] != old
              and item["new_identity"] == identity_of("AC-AAA1", ROW_A_EDIT)
              and item["line"] == 5
              and item["moved"] is True
              and item["match_count"] == 1
              and fired["prefix"] == "AC-AAA1"
              and fired["old_identity"] == old
              and fired["old_line"] is None
              and fired["match_count"] == 0
              and moved["verdict"] == "DRIFT"
              and gone["verdict"] == "GONE")
        if not ok:
            print("  measured: item=%r fired=%r verdicts=%r/%r"
                  % (item, fired, moved["verdict"], gone["verdict"]),
                  flush=True)
        check(ok, "AC-GDR2 DRIFT names both identities, GONE names no line")
    finally:
        shutil.rmtree(moved_world, ignore_errors=True)
        shutil.rmtree(gone_world, ignore_errors=True)


def ac_gdr3():
    """AC-GDR3: exhaustive and disjoint; an empty inert list is NO-DRIFT."""
    kept = identity_of("AC-BBB1", ROW_B)
    moved = identity_of("AC-AAA1", ROW_A)
    ghost = "AC-NONE#deadbeef"
    world = make_world(HEADER + ROW_A_EDIT + ROW_B + PLAIN,
                       declaration([(moved, "docker", "edited row"),
                                    (ghost, "battery", "deleted row"),
                                    (kept, "gpu", "live row")]))
    empty = make_world(HEADER + ROW_A, declaration([]))
    try:
        report = GD.review(world, "tech")
        clean = GD.review(empty, "tech")
        identities = [i["old_identity"] for i in report["drift"]]
        identities += [i["old_identity"] for i in report["gone"]]
        disjoint = len(identities) == len(set(identities))
        # The live AC-BBB1 declaration matches a claimable row, so the gate
        # reports it BLOCKED and it is never inert - only the two stale
        # entries reach this split.
        ok = (report["inert"] == 2
              and report["drift_count"] + report["gone_count"] == report["inert"]
              and disjoint
              and report["moved_count"] == 1
              and report["gone_count"] == 1
              and kept not in identities
              and clean["inert"] == 0
              and clean["verdict"] == "NO-DRIFT"
              and run_cli(empty)[0] == 0)
        if not ok:
            print("  measured: report=%r clean=%r identities=%r"
                  % (report, clean, identities), flush=True)
        check(ok, "AC-GDR3 split exhaustive and disjoint, empty reads NO-DRIFT")
    finally:
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(empty, ignore_errors=True)


def ac_gdr4():
    """AC-GDR4: an absent or unreadable declaration or queue refuses."""
    tech = HEADER + ROW_A
    absent = make_world(tech, None)
    garbage = make_world(tech, None, raw_decl="{not json")
    noqueue = make_world(tech, declaration([]))
    os.unlink(os.path.join(noqueue, "state", "queue", "tech.md"))
    try:
        codes = []
        for target in (absent, garbage, noqueue):
            try:
                GD.review(target, "tech")
                codes.append("no-raise")
            except GD.GateDriftError as exc:
                codes.append(exc.code)
        cli = [run_cli(target) for target in (absent, garbage, noqueue)]
        exits = [item[0] for item in cli]
        claims_drift = [("NO-DRIFT" in item[1]) for item in cli]
        ok = (codes == ["E_MGT_NO_DECL", "E_MGT_BAD_DECL", "E_MGT_NO_QUEUE"]
              and exits == [3, 3, 3]
              and claims_drift == [False, False, False])
        if not ok:
            print("  measured: codes=%r exits=%r claims=%r"
                  % (codes, exits, claims_drift), flush=True)
        check(ok, "AC-GDR4 absent declaration refuses, never a blind NO-DRIFT")
    finally:
        for target in (absent, garbage, noqueue):
            shutil.rmtree(target, ignore_errors=True)


def ac_gdr5():
    """AC-GDR5: CLI 0/2/5, byte-stable --json over pinned keys, zero writes."""
    old = identity_of("AC-AAA1", ROW_A)
    moved_world = make_world(HEADER + ROW_A_EDIT + ROW_B,
                             declaration([(old, "docker", "no docker")]))
    clean_world = make_world(HEADER + ROW_A + ROW_B,
                             declaration([(identity_of("AC-BBB1", ROW_B),
                                           "gpu", "blocked row")]))
    try:
        before = tree_digest(moved_world)
        code_drift, _body = run_cli(moved_world)
        first = run_cli(moved_world, ["--json"])[1]
        second = run_cli(moved_world, ["--json"])[1]
        after = tree_digest(moved_world)
        code_clean = run_cli(clean_world)[0]
        code_bad = run_cli(moved_world, ["--nope"])[0]
        parsed = json.loads(first)
        pinned = tuple(parsed.keys()) == GD.REPORT_KEYS
        drift_pinned = tuple(parsed["drift"][0].keys()) == GD.DRIFT_KEYS
        ok = (code_drift == 2 and code_clean == 0 and code_bad == 5
              and first == second and before == after
              and pinned and drift_pinned
              and parsed["verdict"] == "DRIFT"
              and "DRIFT" in GD.render(GD.review(moved_world, "tech")))
        if not ok:
            print("  measured: drift=%r clean=%r bad=%r stable=%r writes=%r "
                  "pinned=%r/%r"
                  % (code_drift, code_clean, code_bad, first == second,
                     before == after, pinned, drift_pinned), flush=True)
        check(ok, "AC-GDR5 CLI 0/2/5, byte-stable json, zero writes")
    finally:
        shutil.rmtree(moved_world, ignore_errors=True)
        shutil.rmtree(clean_world, ignore_errors=True)


def ac_gdr6():
    """AC-GDR6: pure source, stdlib only, no clock, wired, no-prefix honest."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = ("socket" not in source and "urllib" not in source
              and "http" not in source)
    no_clock = ("import time" not in source and "datetime" not in source
                and "time.time" not in source)
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner) or ("'%s'" % LABEL in runner)
    # A row that carries no criteria prefix keeps its identity ("-"), so the
    # reader says STILL-PRESENT rather than crying drift over a row that has
    # not moved.
    plain_identity = MG.identity_of(None, PLAIN.rstrip("\n"))
    world = make_world(HEADER + PLAIN + ROW_A,
                       declaration([(plain_identity, "toolkit", "no toolkit")]))
    try:
        before = tree_digest(world)
        report = GD.review(world, "tech")
        after = tree_digest(world)
        item = report["drift"][0]
        ok = (ascii_only and no_net and no_clock and wired
              and report["inert"] == 1
              and report["drift_count"] == 1
              and report["gone_count"] == 0
              and report["moved_count"] == 0
              and item["prefix"] == "-"
              and item["new_identity"] == plain_identity
              and item["moved"] is False
              and report["verdict"] == "STILL-PRESENT"
              and run_cli(world)[0] == 0
              and before == after)
        if not ok:
            print("  measured: ascii=%r net=%r clock=%r wired=%r report=%r "
                  "writes=%r"
                  % (ascii_only, no_net, no_clock, wired, report,
                     before == after), flush=True)
        check(ok, "AC-GDR6 pure, wired, a still-present row is not drift")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def main():
    print("gate_drift suite (expected criteria %d)" % EXPECTED_CRITERIA,
          flush=True)
    ac_gdr1()
    ac_gdr2()
    ac_gdr3()
    ac_gdr4()
    ac_gdr5()
    ac_gdr6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())