"""residue_triage_repin suite (R2363; criteria AC-RTRP1..AC-RTRP6 were
pre-registered inside the R2353 seed row of state/queue/tech.md BEFORE this
code existed).

What this proves: the whole-set re-pin the declaration needs at every expiry
is now a writer that only claims what it measured. The entry set, the status
vocabulary and the judge are `residue_triage` own (patched loaders and a
patched live reading move the plan, and this module carries no second
declaration reader and no second status tuple), the dry run is the default and
writes no byte, a moved status refuses instead of being laundered into a fresh
declaration, a declared round that is no longer live refuses unless the caller
says so, the executed write is ONE atomic replace that proves its predicted
size and re-reads TRIAGED, the CLI codes are pinned with a byte-stable --json,
and the module is pure ASCII, stdlib only, reads no clock, touches no network
and holds one write primitive.

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

import residue_triage as RT  # noqa: E402
import residue_triage_repin as RP  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "residue_triage_repin.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-residue-triage-repin"

HEADER = "# queue test world\n\nprose that never becomes a row\n\n"
REASON = "re-pinned at R2351 from one live reading"

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


def entry(round_no, status="DELIVERED", declared_by="R2331", until=2350,
          reason="reviewed at R2331 at its live status"):
    return {
        "round": round_no,
        "status": status,
        "declared_by": declared_by,
        "reason": reason,
        "until": until,
    }


def tech_rows(rounds=("R2300", "R2305", "R2348")):
    out = []
    for number in rounds:
        out.append("- [x] [done 2026-11-01 %s] a closed residue row\n"
                   % number)
    return "".join(out)


def declared(entries=None, head="R2331", reason="reviewed at R2331"):
    return {"declared_by": head, "reason": reason,
            "entries": entries if entries is not None else [
                entry(2300), entry(2305),
                entry(2348, declared_by="R2348", until=2360)]}


def make_world(document=None, raw=None, no_decl=False, tech=None):
    """A throwaway root: state.json, the three queues, the declaration."""
    world = tempfile.mkdtemp(prefix="rtrp-world-")
    os.makedirs(os.path.join(world, "state", "queue"))
    os.makedirs(os.path.join(world, "src", "os"))
    payload = {"tick": 2300, "log": ["R2200 a logged item"]}
    path = os.path.join(world, "src", "os", "state.json")
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload))
    for name, body in (("tech", tech if tech is not None else tech_rows()),
                       ("main", HEADER), ("explore", HEADER)):
        path = os.path.join(world, "state", "queue", name + ".md")
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    if no_decl:
        return world
    path = os.path.join(world, "state", "residue_triage.json")
    if raw is not None:
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(raw)
        return world
    body = json.dumps(document or declared(), ensure_ascii=True, indent=2)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body + "\n")
    return world


def file_map(root):
    """Relative path -> bytes, so 'writes nothing' is measurable."""
    out = {}
    for folder, dirs, names in os.walk(root):
        dirs[:] = sorted(dirs)
        for name in sorted(names):
            path = os.path.join(folder, name)
            out[os.path.relpath(path, root).replace(os.sep, "/")] = \
                open(path, "rb").read()
    return out


def run_cli(args, world=None):
    argv = [sys.executable, MODULE] + list(args)
    if world is not None:
        argv += ["--root", world]
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace"), \
        err.decode("utf-8", "replace")


def refuse(*args, **kwargs):
    """Run a refusing call and hand back (code, detail) or (None, '')."""
    try:
        RP.plan(*args, **kwargs)
    except RP.RepinError as exc:
        return exc.code, exc.detail
    except Exception as exc:  # noqa: BLE001 - a wrong error is not a refusal
        return "WRONG:" + type(exc).__name__, ""
    return None, ""


def code_only(text):
    """The source with comments and docstrings removed.

    A docstring that NAMES a forbidden call is not a call (the R2346 AC-SEG6
    lesson): the assertion reads executable text only.
    """
    without_docstrings = re.sub(r'"""(?:.|\n)*?"""', '', text)
    without_docstrings = re.sub(r"'''(?:.|\n)*?'''", '', without_docstrings)
    return re.sub(r"#[^\n]*", "", without_docstrings)


def ac_rtrp1():
    """Entry set, statuses, judge and the live reading are imports."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    code = code_only(source)
    no_second_reader = (
        "import residue_triage as RT" in code
        and "json.loads" not in code
        and "residue_triage.json" not in code
        and "def load_declaration" not in code
        and "STATUSES" not in code
        and "RT.judge(" in code
        and "RT.live_residue(" in code
        and "RT.load_declaration(" in code)

    # a patched declaration loader moves the entry count the plan reports
    world = make_world()
    saved_loader = RT.load_declaration
    RT.load_declaration = lambda root: {
        "declared_by": 2340, "reason": "synthetic head",
        "entries": [{"round": 2300, "status": "DELIVERED",
                     "declared_by": 2340, "reason": "synthetic",
                     "until": 2350},
                    {"round": 2305, "status": "DELIVERED",
                     "declared_by": 2340, "reason": "synthetic",
                     "until": 2350}]}
    try:
        patched = RP.plan(world, "R2351", "R2370", REASON)
    finally:
        RT.load_declaration = saved_loader

    # a patched live reading moves the plan the same way
    saved_live = RT.live_residue
    RT.live_residue = lambda root: [
        {"round": 2300, "status": "DELIVERED"},
        {"round": 2305, "status": "DELIVERED"},
        {"round": 2348, "status": "DELIVERED"},
        {"round": 2350, "status": "STAMP-ONLY-OPEN"},
    ]
    try:
        moved = RP.plan(world, "R2351", "R2370", REASON)
    finally:
        RT.live_residue = saved_live

    plain = RP.plan(world, "R2351", "R2370", REASON)
    shutil.rmtree(world, ignore_errors=True)
    ok = (no_second_reader
          and patched["entries_before"] == 2
          and moved["entries_after"] == 4
          and [row["status"] for row in moved["statuses"]]
          == ["DELIVERED", "STAMP-ONLY-OPEN"]
          and plain["entries_before"] == 3
          and plain["entries_after"] == 3
          and [row["status"] for row in plain["statuses"]] == ["DELIVERED"])
    if not ok:
        print("  measured: import=%r patched=%r moved=%r plain=%r"
              % (no_second_reader, patched.get("entries_before"),
                 moved.get("statuses"), plain.get("statuses")), flush=True)
    check(ok, "AC-RTRP1 imports")


def ac_rtrp2():
    """The dry run is the default: it plans by number and writes no byte."""
    world = make_world()
    try:
        before = file_map(world)
        report = RP.plan(world, "R2351", "R2370", REASON)
        after = file_map(world)
        counts = sum(row["count"] for row in report["statuses"])
        check(report["verdict"] == "PLANNED"
              and report["executed"] is False
              and report["round"] == "R2351"
              and report["until"] == "R2370"
              and report["reason"] == REASON
              and report["entries_before"] == 3
              and report["entries_after"] == 3
              and report["dropped"] == []
              and counts == report["entries_after"]
              and report["predicted_bytes"] > report["declaration_bytes"]
              and before == after,
              "AC-RTRP2 dry run plans and writes nothing")
        if before != after:
            print("  measured: %r" % [k for k in before
                                      if before.get(k) != after.get(k)],
                  flush=True)
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rtrp3():
    """A moved status refuses: both statuses and both rounds are named."""
    moved = make_world(declared(entries=[
        entry(2300, status="STAMP-ONLY-OPEN"),
        entry(2305),
        entry(2348, declared_by="R2348", until=2360)]))
    ordinary = make_world()
    try:
        before = file_map(moved)
        code, detail = refuse(moved, "R2351", "R2370", REASON)
        untouched = file_map(moved) == before
        # the same world refuses through the CLI as live state, not a crash
        rc, out, _ = run_cli(["--round", "R2351", "--until", "R2370",
                              "--reason", REASON], world=moved)
        clean = RP.plan(ordinary, "R2351", "R2370", REASON)
        check(code == "E_RTRP_DISAGREES"
              and "STAMP-ONLY-OPEN" in detail
              and "DELIVERED" in detail
              and "R2300" in detail
              and "R2351" in detail
              and untouched
              and rc == 2 and "E_RTRP_DISAGREES" in out
              and clean["verdict"] == "PLANNED",
              "AC-RTRP3 a moved status is refused, never laundered")
        if code != "E_RTRP_DISAGREES":
            print("  measured: %r %r" % (code, detail), flush=True)
    finally:
        shutil.rmtree(moved, ignore_errors=True)
        shutil.rmtree(ordinary, ignore_errors=True)


def ac_rtrp4():
    """One atomic replace: size proved, TRIAGED re-read, no temp residue."""
    world = make_world()
    predating = make_world()
    try:
        path = os.path.join(world, "state", "residue_triage.json")
        text = io.open(path, "r", encoding="utf-8").read()
        planned = RP.plan(world, "R2351", "R2370", REASON)
        pinned = RP.plan(world, "R2351", "R2370", REASON, execute=True)
        after = io.open(path, "r", encoding="utf-8").read()
        sized = os.path.getsize(path)
        residue = [name for name in os.listdir(os.path.dirname(path))
                   if RP.TEMP_SUFFIX in name or name.endswith(".tmp")]
        reread = RT.read(world, "R2351")
        document = json.loads(after)
        every_until = set(row["until"] for row in document["entries"])
        every_by = set(row["declared_by"] for row in document["entries"])
        source = io.open(MODULE, "r", encoding="utf-8").read()
        writes = code_only(source).count("os.replace(")
        before_refusal = file_map(predating)
        bad_until = refuse(predating, "R2351", "R2300", REASON)
        stale = file_map(predating) == before_refusal
        check(pinned["verdict"] == "PINNED"
              and pinned["executed"] is True
              and sized == planned["predicted_bytes"]
              == pinned["predicted_bytes"]
              and sized != len(text.encode("utf-8"))
              and not residue
              and reread["verdict"] == "TRIAGED"
              and reread["untriaged"] == 0
              and document["declared_by"] == 2351
              and every_until == {2370}
              and every_by == {2351}
              and writes == 1
              and bad_until[0] == "E_RTRP_UNTIL_PREDATES"
              and "R2300" in bad_until[1]
              and stale,
              "AC-RTRP4 one atomic replace, size proved, TRIAGED")
        if not (sized == planned["predicted_bytes"] and not residue):
            print("  measured: sized=%d predicted=%d residue=%r"
                  % (sized, planned["predicted_bytes"], residue), flush=True)
    finally:
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(predating, ignore_errors=True)


def ac_rtrp5():
    """CLI codes are pinned and --json is byte-stable in the pinned order."""
    planned = make_world()
    pinned = make_world()
    moved = make_world(declared(entries=[
        entry(2300, status="STAMP-ONLY-OPEN"),
        entry(2305),
        entry(2348, declared_by="R2348", until=2360)]))
    unmatched = make_world(tech=tech_rows(rounds=("R2300", "R2305")))
    missing = make_world(no_decl=True)
    unreadable = make_world(raw="{not json")
    try:
        code0, out0, _ = run_cli(["--round", "R2351", "--until", "R2370",
                                  "--reason", REASON], world=planned)
        code0j, out_json, _ = run_cli(["--round", "R2351", "--until", "R2370",
                                       "--reason", REASON, "--json"],
                                      world=planned)
        again, out_again, _ = run_cli(["--round", "R2351", "--until", "R2370",
                                       "--reason", REASON, "--json"],
                                      world=planned)
        code0x, out_x, _ = run_cli(["--round", "R2351", "--until", "R2370",
                                    "--reason", REASON, "--execute"],
                                   world=pinned)
        code2, out2, _ = run_cli(["--round", "R2351", "--until", "R2370",
                                  "--reason", REASON], world=moved)
        code2b, out2b, _ = run_cli(["--round", "R2351", "--until", "R2370",
                                    "--reason", REASON], world=unmatched)
        code3, out3, _ = run_cli(["--round", "R2351", "--until", "R2370",
                                  "--reason", REASON], world=missing)
        code3b, out3b, _ = run_cli(["--round", "R2351", "--until", "R2370",
                                    "--reason", REASON], world=unreadable)
        code5, out5, _ = run_cli(["--round", "R2351"], world=planned)
        code5b, out5b, _ = run_cli(["--round", "R2351", "--until", "R2300",
                                    "--reason", REASON], world=planned)
        body = json.loads(out_json) if out_json.strip() else {}
        check(code0 == 0 and "PLANNED" in out0
              and code0j == 0
              and tuple(body.keys()) == RP.PLAN_KEYS
              and body.get("verdict") == "PLANNED"
              and again == 0 and out_again == out_json
              and code0x == 0 and "PINNED" in out_x
              and code2 == 2 and "E_RTRP_DISAGREES" in out2
              and code2b == 2 and "E_RTRP_UNMATCHED" in out2b
              and "R2348" in out2b
              and code3 == 3 and "E_RTRP_UNPINNED" in out3
              and code3b == 3 and "E_RTR_UNREADABLE" in out3b
              and code5 == 5 and "E_RTRP_BAD_ARGS" in out5
              and code5b == 5 and "E_RTRP_UNTIL_PREDATES" in out5b,
              "AC-RTRP5 CLI codes")
        if tuple(body.keys()) != RP.PLAN_KEYS:
            print("  measured keys: %r" % (tuple(body.keys()),), flush=True)
        if again != 0 or out_again != out_json:
            print("  measured: json not byte-stable", flush=True)
    finally:
        for world in (planned, pinned, moved, unmatched, missing, unreadable):
            shutil.rmtree(world, ignore_errors=True)


def ac_rtrp6():
    """Pure ASCII, stdlib only, no clock, no network, wired once."""
    raw = io.open(MODULE, "rb").read()
    try:
        text = raw.decode("ascii")
        ascii_ok = True
    except (UnicodeDecodeError, ValueError):
        text = raw.decode("utf-8", "replace")
        ascii_ok = False
    code = code_only(text)
    imports = set(re.findall(r"^import (\w+)", code, re.M))
    forbidden = ("socket", "urllib", "http.client", "requests",
                 "import time", "time.time", "strftime", "datetime",
                 "os.remove", "unlink", "rmtree", "shutil")
    clean = [token for token in forbidden if token in code]
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('("%s"' % LABEL) in runner and \
        "test_residue_triage_repin.py" in runner
    check(ascii_ok
          and imports <= {"json", "os", "sys", "residue_triage"}
          and not clean
          and wired,
          "AC-RTRP6 purity and wiring")
    if clean or not ascii_ok or not wired:
        print("  measured: ascii=%r clean=%r wired=%r imports=%r"
              % (ascii_ok, clean, wired, sorted(imports)), flush=True)


def main():
    for name in ("ac_rtrp1", "ac_rtrp2", "ac_rtrp3", "ac_rtrp4", "ac_rtrp5",
                 "ac_rtrp6"):
        globals()[name]()
    total = PASSES + FAILS
    verdict = "PASS" if FAILS == 0 and total == EXPECTED_CRITERIA else "FAIL"
    print("SUITE %s %d/%d" % (verdict, PASSES, total))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())