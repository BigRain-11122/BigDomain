"""machine_gate suite (R2286; criteria AC-MGT1..AC-MGT6 were pre-registered
inside the R2270 seed row of state/queue/tech.md BEFORE this code existed).

What this proves: a machine gate becomes data with a date instead of the
operator's memory. The head law is imported from queue_head - every
candidate comes out of queue_head.head_text and the reader never carries a
second row predicate - and the suite proves the import by patching that law
and watching the offer move.

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

import machine_gate as MG  # noqa: E402
import queue_head as QH  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "machine_gate.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-machine-gate"

HEADER = "# queue test world\n\nprose that never becomes a row\n\n"
ROW_A = "- [ ] alpha row: Criteria prefix AC-AAA1 pinned here first\n"
ROW_B = "- [ ] beta row: Criteria prefix AC-BBB1 pinned here first\n"
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


def declaration(entries, version=1):
    """A declaration body built from (identity, capability, reason) legs."""
    gates = []
    for identity, capability, reason in entries:
        gates.append({"identity": identity,
                      "capability": capability,
                      "reason": reason,
                      "declared_by": "R2286"})
    return {"version": version,
            "declared_by": "R2286",
            "reason": "suite declaration",
            "gates": gates}


def make_world(tech, decl=None, raw_decl=None):
    """Build a temp root with the three queue files and one declaration."""
    world = tempfile.mkdtemp(prefix="bigdomain-mgt-")
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


def row_identity(body):
    return MG.identity_of("AC-AAA1", body.rstrip("\n"))


def run_cli(world, extra=()):
    argv = [sys.executable, MODULE, "--gate", "tech", "--root", world]
    argv.extend(extra)
    proc = subprocess.run(argv, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def ac_mgt1():
    """AC-MGT1: the head law is imported and a patched head flows through."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    imported = "QH.head_text(" in source
    no_row_law = ("def is_open_row" not in source
                  and "def is_done_row" not in source
                  and 'startswith("- [' not in source)
    tech = HEADER + ROW_A + ROW_B
    world = make_world(tech, declaration([]))
    try:
        live = MG.gate(world, "tech")
        saved = QH.head_text

        def constant(name, rel, text):
            return {"head": {"line": 4, "prefix": "AC-PATCH",
                             "text": "patched row"}}

        def once(name, rel, text):
            if not once.done:
                once.done = True
                return constant(name, rel, text)
            return {"head": None}
        once.done = False
        try:
            QH.head_text = once
            patched = MG.gate(world, "tech")
        finally:
            QH.head_text = saved
        ok = (imported and no_row_law
              and live["offered"]["line"] == 5
              and patched["offered"]["line"] == 4
              and patched["offered"]["prefix"] == "AC-PATCH"
              and live["offered"]["prefix"] == "AC-AAA1")
        if not ok:
            print("  measured: imported=%r no_row_law=%r live=%r patched=%r"
                  % (imported, no_row_law, live["offered"],
                     patched["offered"]), flush=True)
        check(ok, "AC-MGT1 head law imported, a patched head flows through")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_mgt2():
    """AC-MGT2: a blocker names identity/capability/reason; bad input closes."""
    tech = HEADER + ROW_A + ROW_B
    identity = row_identity(ROW_A)
    world = make_world(tech, declaration([(identity, "docker", "no docker")]))
    bad_cap = make_world(tech, declaration([(identity, "spaceship", "nope")]))
    missing = make_world(tech, declaration([]))
    with io.open(os.path.join(missing, "state", "machine_gates.json"), "w",
                 encoding="utf-8", newline="\n") as handle:
        body = declaration([])
        body["gates"] = [{"identity": identity, "capability": "docker",
                          "reason": "no docker"}]
        handle.write(json.dumps(body, ensure_ascii=True))
    unknown = make_world(tech, declaration([]))
    with io.open(os.path.join(unknown, "state", "machine_gates.json"), "w",
                 encoding="utf-8", newline="\n") as handle:
        body = declaration([])
        body["extra"] = "nope"
        handle.write(json.dumps(body, ensure_ascii=True))
    try:
        live = MG.gate(world, "tech")
        blocked = live["blocked"][0]
        named = (blocked["identity"] == identity
                 and blocked["capability"] == "docker"
                 and blocked["reason"] == "no docker"
                 and blocked["declared_by"] == "R2286")
        codes = []
        for target in (bad_cap, missing, unknown):
            try:
                MG.gate(target, "tech")
                codes.append("no-raise")
            except MG.MachineGateError as exc:
                codes.append(exc.code)
        ok = (named and codes == ["E_MGT_BAD_CAPABILITY", "E_MGT_BAD_ENTRY",
                                  "E_MGT_BAD_DECL"])
        if not ok:
            print("  measured: named=%r codes=%r blocked=%r"
                  % (named, codes, blocked), flush=True)
        check(ok, "AC-MGT2 blocker names its four fields, bad input closes")
    finally:
        for target in (world, bad_cap, missing, unknown):
            shutil.rmtree(target, ignore_errors=True)


def ac_mgt3():
    """AC-MGT3: a blocked row is never offered; the next row is."""
    tech = HEADER + ROW_A + ROW_B
    identity = row_identity(ROW_A)
    world = make_world(tech, declaration([(identity, "docker", "no docker")]))
    try:
        report = MG.gate(world, "tech")
        offered = report["offered"]
        blocked = report["blocked"]
        ok = (offered is not None
              and offered["prefix"] == "AC-BBB1"
              and offered["line"] == 6
              and report["blocked_rows"] == 1
              and len(blocked) == 1
              and blocked[0]["prefix"] == "AC-AAA1"
              and blocked[0]["line"] == 5
              and blocked[0]["capability"] == "docker"
              and identity not in [offered["identity"]]
              and report["candidates"] == 2
              and report["verdict"] == "OFFERED"
              and "BLOCK" in MG.render(report))
        if not ok:
            print("  measured: offered=%r blocked=%r candidates=%r"
                  % (offered, blocked, report["candidates"]), flush=True)
        check(ok, "AC-MGT3 blocked row reported, the next row is offered")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_mgt4():
    """AC-MGT4: a missing or unreadable declaration refuses the reading."""
    tech = HEADER + ROW_A
    absent = make_world(tech, None)
    garbage = make_world(tech, None, raw_decl="{not json")
    noqueue = make_world(tech, declaration([]))
    os.unlink(os.path.join(noqueue, "state", "queue", "tech.md"))
    try:
        codes = []
        for target in (absent, garbage, noqueue):
            try:
                MG.gate(target, "tech")
                codes.append("no-raise")
            except MG.MachineGateError as exc:
                codes.append(exc.code)
        # the same three worlds through the CLI: exit 3, never an offer.
        cli = [run_cli(target)[0] for target in (absent, garbage, noqueue)]
        ok = (codes == ["E_MGT_NO_DECL", "E_MGT_BAD_DECL", "E_MGT_NO_QUEUE"]
              and cli == [3, 3, 3])
        if not ok:
            print("  measured: codes=%r cli=%r" % (codes, cli), flush=True)
        check(ok, "AC-MGT4 missing declaration refuses, never a blind offer")
    finally:
        for target in (absent, garbage, noqueue):
            shutil.rmtree(target, ignore_errors=True)


def ac_mgt5():
    """AC-MGT5: CLI codes, a byte-stable --json, and zero writes."""
    tech = HEADER + ROW_A + ROW_B
    identity = row_identity(ROW_A)
    world = make_world(tech, declaration([(identity, "docker", "no docker")]))
    all_blocked = make_world(HEADER + ROW_A,
                             declaration([(row_identity(ROW_A), "gpu",
                                           "no gpu")]))
    try:
        before = tree_digest(world)
        code_open, _body = run_cli(world)
        first = run_cli(world, ["--json"])[1]
        second = run_cli(world, ["--json"])[1]
        after = tree_digest(world)
        code_none, _body2 = run_cli(all_blocked)
        code_bad = run_cli(world, ["--nope"])[0]
        parsed = json.loads(first)
        pinned = tuple(parsed.keys()) == MG.REPORT_KEYS
        offer_pinned = tuple(parsed["offered"].keys()) == MG.OFFER_KEYS
        block_pinned = tuple(parsed["blocked"][0].keys()) == MG.BLOCK_KEYS
        ok = (code_open == 0 and code_none == 2 and code_bad == 5
              and first == second and before == after
              and pinned and offer_pinned and block_pinned
              and parsed["verdict"] == "OFFERED")
        if not ok:
            print("  measured: open=%r none=%r bad=%r stable=%r writes=%r "
                  "pinned=%r/%r/%r"
                  % (code_open, code_none, code_bad, first == second,
                     before == after, pinned, offer_pinned, block_pinned),
                  flush=True)
        check(ok, "AC-MGT5 CLI 0/2/5, byte-stable json, zero writes")
    finally:
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(all_blocked, ignore_errors=True)


def ac_mgt6():
    """AC-MGT6: pure source, stdlib only, no clock, wired, inert honest."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = ("socket" not in source and "urllib" not in source
              and "http" not in source)
    no_clock = ("import time" not in source and "datetime" not in source
                and "time.time" not in source)
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner) or ("'%s'" % LABEL in runner)
    tech = HEADER + PLAIN + ROW_A
    plain_identity = MG.identity_of(None, PLAIN.rstrip("\n"))
    gone_identity = "AC-GONE#deadbeef"
    world = make_world(tech, declaration([(plain_identity, "toolkit",
                                           "no toolkit"),
                                          (gone_identity, "battery",
                                           "row is gone")]))
    try:
        before = tree_digest(world)
        report = MG.gate(world, "tech")
        after = tree_digest(world)
        inert = report["inert"]
        ok = (ascii_only and no_net and no_clock and wired
              and report["offered"]["line"] == 6
              and report["declarations"] == 2
              and report["blocked_rows"] == 0
              and len(inert) == 2
              and inert[0]["identity"] == plain_identity
              and inert[0]["line"] == 5
              and inert[1]["identity"] == gone_identity
              and inert[1]["line"] is None
              and before == after)
        if not ok:
            print("  measured: ascii=%r net=%r clock=%r wired=%r inert=%r "
                  "writes=%r"
                  % (ascii_only, no_net, no_clock, wired, inert,
                     before == after), flush=True)
        check(ok, "AC-MGT6 pure, wired, unmatchable rows read INERT honestly")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def main():
    print("machine_gate suite (expected criteria %d)" % EXPECTED_CRITERIA,
          flush=True)
    ac_mgt1()
    ac_mgt2()
    ac_mgt3()
    ac_mgt4()
    ac_mgt5()
    ac_mgt6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())