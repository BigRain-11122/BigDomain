"""residue_triage suite (R2310; criteria AC-RTR1..AC-RTR6 were pre-registered
inside the R2298 seed row of state/queue/tech.md BEFORE this code existed).

What this proves: the stamp residue is now a dated declaration instead of
prose re-typed every window. The residue list and every status come from
`stamp_residue` itself, a patched reading flows straight through, an entry for
a round the live reader no longer lists is inert, a status disagreement names
both readings and keeps the debt, an expired entry hands its round back naming
its until round, a missing declaration reads UNPINNED with the full debt, and
the CLI refuses with its own codes while writing nothing.

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

import residue_triage as RT  # noqa: E402
import stamp_residue as SR  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "residue_triage.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-residue-triage"

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


def make_world(done_rounds=(905,), log_rounds=(), declaration=None,
               raw=None):
    """A temp root with src/os/state.json, state/queue/tech.md and a pin."""
    world = tempfile.mkdtemp(prefix="bigdomain-rtr-")
    os.makedirs(os.path.join(world, "src", "os"))
    os.makedirs(os.path.join(world, "state", "queue"))
    rows = []
    for number in done_rounds:
        rows.append("- [x] [done 2026-11-01 R%03d] a closed row\n" % number)
    with io.open(os.path.join(world, "state", "queue", "tech.md"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write("".join(rows))
    log = ["R%03d log item" % number for number in log_rounds]
    state = {"tick": max(list(done_rounds) + list(log_rounds) + [1]),
             "log": log}
    with io.open(os.path.join(world, "src", "os", "state.json"), "w",
                 encoding="utf-8", newline="\n") as handle:
        json.dump(state, handle, indent=2)
        handle.write("\n")
    path = os.path.join(world, RT.DECLARATION_PATH)
    if raw is not None:
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(raw)
    elif declaration is not None:
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(declaration, handle, indent=2, sort_keys=False)
            handle.write("\n")
    return world


def declaration(entries=None, declared_by="R2310",
                reason="pinned for the suite"):
    """A well-shaped declaration."""
    if entries is None:
        entries = []
    return {"declared_by": declared_by, "reason": reason, "entries": entries}


def entry(number, status="DELIVERED", until=2330, declared_by="R2310"):
    """One well-shaped entry."""
    return {"round": number, "status": status, "declared_by": declared_by,
            "reason": "reviewed", "until": until}


def tree_digest(world):
    """Every file under the world with its size and bytes."""
    out = []
    for root, dirs, files in os.walk(world):
        dirs.sort()
        for name in sorted(files):
            path = os.path.join(root, name)
            with io.open(path, "rb") as handle:
                data = handle.read()
            out.append((os.path.relpath(path, world), len(data), hash(data)))
        for name in sorted(dirs):
            out.append((os.path.relpath(os.path.join(root, name), world),
                        -1, 0))
    return sorted(out)


def run_cli(world, args=None):
    """Run the module as a child interpreter against one world."""
    argv = [sys.executable, MODULE, "--check", "--root", world]
    if args:
        argv.extend(args)
    proc = subprocess.run(argv, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def ac_rtr1():
    """AC-RTR1: list and statuses imported from stamp_residue, patch flows."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    no_private = "DELIVERED" not in source and "STAMP-ONLY-OPEN" not in source
    same_statuses = RT.SR.STATUSES is SR.STATUSES
    original = SR.read
    patched = {
        "round_count": 1,
        "delivered": 0,
        "stamp_only_open": 1,
        "no_hit": 0,
        "verdict": "RESIDUE",
        "rounds": [{"round": 907, "hit_count": 1, "closed_hits": 0,
                    "open_hits": 1, "status": "STAMP-ONLY-OPEN", "hits": []}],
    }
    world = make_world(declaration=declaration(
        [entry(907, status="STAMP-ONLY-OPEN")]))
    try:
        SR.read = lambda root: patched
        flowed = RT.read(world, "R2310")
        bad_status = None
        broken = {"rounds": [{"round": 907, "status": "NOT-A-STATUS"}]}
        SR.read = lambda root: broken
        try:
            RT.read(world, "R2310")
        except RT.ResidueTriageError as exc:
            bad_status = exc.code
    finally:
        SR.read = original
        shutil.rmtree(world, ignore_errors=True)
    ok = (no_private and same_statuses
          and flowed["residue_count"] == 1 and flowed["triaged"] == 1
          and flowed["verdict"] == "TRIAGED"
          and flowed["entries"][0]["declared_status"] == "STAMP-ONLY-OPEN"
          and bad_status == "E_RTR_BAD_STATUS")
    if not ok:
        print("  measured: private=%r same=%r flowed=%r bad=%r"
              % (no_private, same_statuses, flowed, bad_status), flush=True)
    check(ok, "AC-RTR1 residue and statuses imported, patch flows through")


def ac_rtr2():
    """AC-RTR2: an entry outside the live residue is UNMATCHED and inert."""
    world = make_world(done_rounds=(905,),
                       declaration=declaration([entry(909)]))
    try:
        report = RT.read(world, "R2310")
        rendered = RT.render(report)
        ok = (report["entries"][0]["state"] == "UNMATCHED"
              and report["entries"][0]["live_status"] == "-"
              and report["unmatched"] == 1
              and report["residue"] == [905]
              and report["untriaged"] == 1
              and report["triaged"] == 0
              and report["verdict"] == "RESIDUE"
              and "ENTRY R909 state=UNMATCHED" in rendered)
        if not ok:
            print("  measured: %r" % (report,), flush=True)
        check(ok, "AC-RTR2 unmatched entry never covers the live debt")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rtr3():
    """AC-RTR3: a status disagreement names both readings, keeps the debt."""
    world = make_world(done_rounds=(905,), declaration=declaration(
        [entry(905, status="STAMP-ONLY-OPEN")]))
    try:
        report = RT.read(world, "R2310")
        rendered = RT.render(report)
        ok = (report["entries"][0]["state"] == "DISAGREES"
              and report["entries"][0]["declared_status"] == "STAMP-ONLY-OPEN"
              and report["entries"][0]["live_status"] == "DELIVERED"
              and report["disagrees"] == 1
              and report["residue"] == [905]
              and report["verdict"] == "RESIDUE"
              and "state=DISAGREES declared=STAMP-ONLY-OPEN live=DELIVERED"
              in rendered)
        if not ok:
            print("  measured: %r" % (report,), flush=True)
        check(ok, "AC-RTR3 disagreement names both statuses")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rtr4():
    """AC-RTR4: expiry returns the round naming until; missing reads UNPINNED."""
    expired = make_world(done_rounds=(905,), declaration=declaration(
        [entry(905, until=2300)]))
    unpinned = make_world(done_rounds=(905, 906))
    try:
        aged = RT.read(expired, "R2310")
        rendered = RT.render(aged)
        blank = RT.read(unpinned, "R2310")
        ok = (aged["entries"][0]["state"] == "EXPIRED"
              and aged["expired"] == 1
              and aged["residue"] == [905]
              and aged["verdict"] == "RESIDUE"
              and "until=R2300" in rendered
              and blank["declaration"] == "UNPINNED"
              and blank["declared_by"] is None
              and blank["residue"] == [905, 906]
              and blank["untriaged"] == 2
              and blank["triaged"] == 0
              and blank["verdict"] == "RESIDUE")
        if not ok:
            print("  measured: aged=%r blank=%r" % (aged, blank), flush=True)
        check(ok, "AC-RTR4 expiry names until, missing declaration is UNPINNED")
    finally:
        shutil.rmtree(expired, ignore_errors=True)
        shutil.rmtree(unpinned, ignore_errors=True)


def ac_rtr5():
    """AC-RTR5: CLI exits 0/2/3/5, byte-stable json, zero writes."""
    good = make_world(done_rounds=(905,),
                      declaration=declaration([entry(905)]))
    unpinned = make_world(done_rounds=(905,))
    broken = make_world(done_rounds=(905,), raw="{not json")
    badshape = make_world(done_rounds=(905,),
                          raw='{"declared_by": "R2310"}')
    faceless = tempfile.mkdtemp(prefix="bigdomain-rtr-empty-")
    try:
        before = [tree_digest(w) for w in (good, unpinned, broken, badshape)]
        code_ok = run_cli(good, ["--round", "R2310"])[0]
        code_residue = run_cli(unpinned, ["--round", "R2310"])[0]
        code_unreadable = run_cli(broken, ["--round", "R2310"])[0]
        code_badshape = run_cli(badshape, ["--round", "R2310"])[0]
        code_badstate = run_cli(faceless, ["--round", "R2310"])[0]
        code_flag = run_cli(good, ["--round", "R2310", "--nope"])[0]
        code_no_round = run_cli(good)[0]
        code_no_check = subprocess.run(
            [sys.executable, MODULE, "--root", good, "--round", "R2310"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT).returncode
        first = run_cli(good, ["--round", "R2310", "--json"])[1]
        second = run_cli(good, ["--round", "R2310", "--json"])[1]
        parsed = json.loads(first)
        pinned = tuple(parsed.keys()) == RT.REPORT_KEYS
        after = [tree_digest(w) for w in (good, unpinned, broken, badshape)]
        ok = (code_ok == 0 and code_residue == 2 and code_unreadable == 3
              and code_badshape == 3 and code_badstate == 3
              and code_flag == 5 and code_no_round == 5
              and code_no_check == 5 and first == second and pinned
              and before == after and parsed["verdict"] == "TRIAGED")
        if not ok:
            print("  measured: codes=%r stable=%r pinned=%r writes=%r"
                  % ((code_ok, code_residue, code_unreadable, code_badshape,
                      code_badstate, code_flag, code_no_round, code_no_check),
                     first == second, pinned, before == after), flush=True)
        check(ok, "AC-RTR5 CLI codes, byte-stable pinned json, zero writes")
    finally:
        for world in (good, unpinned, broken, badshape, faceless):
            shutil.rmtree(world, ignore_errors=True)


def ac_rtr6():
    """AC-RTR6: pure ASCII, stdlib only, wired, and the live debt is clean."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = ("socket" not in source and "urllib" not in source
              and "http" not in source)
    no_clock = ("import time" not in source and "datetime" not in source)
    stdlib_only = True
    for line in source.splitlines():
        text = line.strip()
        if text.startswith("import ") and " " not in text[7:]:
            name = text[7:].strip()
            if name not in ("json", "os", "sys"):
                stdlib_only = False
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner) or ("'%s'" % LABEL in runner)
    live = RT.read(REPO, "R2310")
    rendered = RT.render(live)
    ok = (ascii_only and no_net and no_clock and stdlib_only and wired
          and live["declaration"] == "PINNED"
          and live["verdict"] == "TRIAGED"
          and live["residue_count"] >= 1
          and live["untriaged"] == 0
          and "RESIDUE TRIAGE declaration=PINNED" in rendered)
    if not ok:
        print("  measured: ascii=%r net=%r clock=%r stdlib=%r wired=%r "
              "live=%s" % (ascii_only, no_net, no_clock, stdlib_only, wired,
                           RT.one_line(live)), flush=True)
    check(ok, "AC-RTR6 pure source, wired, live residue fully triaged")


def main():
    print("residue_triage suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_rtr1()
    ac_rtr2()
    ac_rtr3()
    ac_rtr4()
    ac_rtr5()
    ac_rtr6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())