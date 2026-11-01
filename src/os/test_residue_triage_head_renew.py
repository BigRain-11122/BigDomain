"""residue_triage_head_renew suite (R2351; criteria AC-RTRH1..AC-RTRH6 were
pre-registered inside the R2350 seed row of state/queue/tech.md BEFORE this
code existed).

What this proves: the triage declaration head can finally be renewed by a
writer that only claims what it measured. The entry set, the status
vocabulary and the live residue are imported from residue_triage and the head
claim from residue_triage_decl_reason (patching any of them moves the
renewal, and this module carries no second declaration reader), the dry run is
the default and writes no byte, a renewal is refused before any byte when a
declared entry disagrees with the live reading, when a live residue round is
still undeclared, or when the round would predate an entry's own declared_by,
the executed renewal is one atomic splice that leaves every entry
byte-identical and proves its own predicted size, the CLI codes are pinned
with a byte-stable --json, and the module is pure ASCII, stdlib only, reads no
clock, touches no network and holds no delete path.

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

import residue_triage as RT  # noqa: E402
import residue_triage_decl_reason as DR  # noqa: E402
import residue_triage_head_renew as HR  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "residue_triage_head_renew.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-residue-triage-head-renew"

HEADER = "# queue test world\n\nprose that never becomes a row\n\n"

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


def stale_entries():
    """The live R2350 shape: two entries at the head, one later append."""
    return [entry(2300), entry(2305),
            entry(2348, declared_by="R2348", until=2360)]


def tech_rows(rounds=("R2300", "R2305", "R2348")):
    out = []
    for number in rounds:
        out.append("- [x] [done 2026-11-01 %s] a closed residue row\n"
                   % number)
    return "".join(out)


def make_world(entries=None, head="R2331", reason="renewed at R2331",
               tech=None, raw=None, no_decl=False, live_rounds=None):
    """A throwaway root: state.json, the three queues, the declaration."""
    world = tempfile.mkdtemp(prefix="rtrh-world-")
    os.makedirs(os.path.join(world, "state", "queue"))
    os.makedirs(os.path.join(world, "src", "os"))
    payload = {"tick": 2300, "log": ["R2200 a logged item"]}
    path = os.path.join(world, "src", "os", "state.json")
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload))
    bodies = {"tech": tech if tech is not None else tech_rows(
        live_rounds or ("R2300", "R2305", "R2348")),
        "main": HEADER,
        "explore": HEADER}
    for name in bodies:
        path = os.path.join(world, "state", "queue", name + ".md")
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(bodies[name])
    if no_decl:
        return world
    path = os.path.join(world, "state", "residue_triage.json")
    if raw is not None:
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(raw)
        return world
    document = {"declared_by": head, "reason": reason,
                "entries": entries or stale_entries()}
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(document, ensure_ascii=True, indent=2) + "\n")
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


def tail_of(text):
    """Everything from the top-level entries key onward, byte for byte."""
    match = HR.ENTRIES_MARKER.search(text)
    return "" if match is None else text[match.start():]


def run_cli(args, world=None):
    argv = [sys.executable, MODULE] + list(args)
    if world is not None:
        argv += ["--root", world]
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace"), \
        err.decode("utf-8", "replace")


def refuse(callable_, *args, **kwargs):
    """Run a refusing call and hand back (code, detail) or (None, '')."""
    try:
        callable_(*args, **kwargs)
    except HR.RenewError as exc:
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


def ac_rtrh1():
    """Entry set, statuses, live residue and the head reading are imported."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    code = code_only(source)
    no_second_reader = ("import residue_triage as RT" in code
                        and "import residue_triage_decl_reason as DR" in code
                        and "json.loads" not in code
                        and "residue_triage.json" not in code
                        and "def load_declaration" not in code
                        and HR.DECLARATION_PATH == RT.DECLARATION_PATH)

    # a patched declaration loader moves the OLD head the plan names
    world = make_world()
    synthetic = {"declared_by": 2400, "reason": "synthetic head",
                 "entries": [
                     {"round": 2300, "status": "DELIVERED",
                      "declared_by": 2400, "reason": "synthetic",
                      "until": 2350},
                     {"round": 2305, "status": "DELIVERED",
                      "declared_by": 2400, "reason": "synthetic",
                      "until": 2350},
                     {"round": 2348, "status": "DELIVERED",
                      "declared_by": 2400, "reason": "synthetic",
                      "until": 2360},
                 ]}
    saved_loader = RT.load_declaration
    RT.load_declaration = lambda root: synthetic
    try:
        patched = HR.plan(world, "R2401")
    finally:
        RT.load_declaration = saved_loader

    # a patched head reading moves the verdict: HEAD-CURRENT means NOOP
    saved_head = DR.read
    DR.read = lambda root: {"declaration": "PINNED",
                            "declared_by": "R2331",
                            "head_until": "R2350",
                            "head_reason": "patched",
                            "entries": 3,
                            "breaks": [],
                            "first_break": "-",
                            "verdict": "HEAD-CURRENT"}
    try:
        noop = HR.plan(world, "R2351")
    finally:
        DR.read = saved_head

    # a patched live residue moves the refusal
    saved_live = RT.live_residue
    RT.live_residue = lambda root: [
        {"round": 2300, "status": "STAMP-ONLY-OPEN"},
        {"round": 2305, "status": "DELIVERED"},
        {"round": 2348, "status": "DELIVERED"},
    ]
    try:
        moved = refuse(HR.plan, world, "R2351")
    finally:
        RT.live_residue = saved_live

    plain = HR.plan(world, "R2351")
    shutil.rmtree(world, ignore_errors=True)
    if not (no_second_reader
            and patched["old_declared_by"] == "R2400"
            and noop["verdict"] == "NOOP"
            and noop["executed"] is False
            and moved[0] == "E_RTRH_DISAGREES" and "R2300" in moved[1]
            and plain["verdict"] == "PLANNED"
            and plain["old_declared_by"] == "R2331"):
        print("  measured: import=%r patched=%r noop=%r moved=%r plain=%r"
              % (no_second_reader, patched.get("old_declared_by"),
                 noop.get("verdict"), moved[0], plain.get("verdict")),
              flush=True)
    check(no_second_reader
          and patched["old_declared_by"] == "R2400"
          and noop["verdict"] == "NOOP"
          and noop["executed"] is False
          and moved[0] == "E_RTRH_DISAGREES" and "R2300" in moved[1]
          and plain["verdict"] == "PLANNED",
          "AC-RTRH1 imports")


def ac_rtrh2():
    """The dry run is the default: it plans by number and writes no byte."""
    world = make_world()
    try:
        before = file_map(world)
        report = HR.plan(world, "R2351")
        after = file_map(world)
        execute_world = make_world()
        try:
            renewed = HR.plan(execute_world, "R2351", execute=True)
            written = os.path.getsize(
                os.path.join(execute_world, "state",
                             "residue_triage.json"))
        finally:
            shutil.rmtree(execute_world, ignore_errors=True)
        stats = report["statuses"]
        check(report["verdict"] == "PLANNED"
              and report["executed"] is False
              and report["old_declared_by"] == "R2331"
              and report["old_until"] == "R2350"
              and report["new_declared_by"] == "R2351"
              and report["new_until"] == "R2350"
              and report["entries"] == 3
              and stats == [{"status": "DELIVERED", "count": 3}]
              and report["remaining_breaks"] == 1
              and report["remaining_first"] == "R2348"
              and report["predicted_bytes"] > report["old_bytes"]
              and report["predicted_bytes"] == renewed["predicted_bytes"]
              and written == renewed["predicted_bytes"]
              and before == after,
              "AC-RTRH2 dry run plans and writes nothing")
        if before != after:
            print("  measured: %r" % [k for k in before
                                      if before.get(k) != after.get(k)],
                  flush=True)
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rtrh3():
    """Three refusals, each naming its rounds, each leaving the tree untouched."""
    disagree = make_world(entries=[entry(2300, status="STAMP-ONLY-OPEN"),
                                   entry(2305),
                                   entry(2348, declared_by="R2348",
                                         until=2360)])
    undeclared = make_world(live_rounds=("R2300", "R2305", "R2348", "R2307"))
    predates = make_world()
    outcomes = []
    trees = []
    for world, round_text in ((disagree, "R2351"), (undeclared, "R2351"),
                              (predates, "R2340")):
        before = file_map(world)
        outcomes.append(refuse(HR.plan, world, round_text, False))
        trees.append(before == file_map(world))
    for world in (disagree, undeclared, predates):
        shutil.rmtree(world, ignore_errors=True)
    codes = [item[0] for item in outcomes]
    details = " | ".join(item[1] for item in outcomes)
    check(codes == ["E_RTRH_DISAGREES", "E_RTRH_UNDECLARED",
                    "E_RTRH_HEAD_PREDATES"]
          and "R2300" in outcomes[0][1]
          and "R2307" in outcomes[1][1]
          and "R2348" in outcomes[2][1]
          and all(trees),
          "AC-RTRH3 refusals name their rounds")


def ac_rtrh4():
    """One atomic splice: entries byte-identical, size proved, no residue."""
    world = make_world()
    try:
        path = os.path.join(world, "state", "residue_triage.json")
        original = io.open(path, "r", encoding="utf-8").read()
        planned = HR.plan(world, "R2351")
        renewed = HR.plan(world, "R2351", execute=True)
        after = io.open(path, "r", encoding="utf-8").read()
        sized = os.path.getsize(path)
        residue = [name for name in os.listdir(os.path.dirname(path))
                   if name.endswith(".renew-part") or name.endswith(".tmp")]
        reread = DR.read(world)
        kinds = [row["kind"] for row in reread["breaks"]]
        head_region = after[:len(after) - len(tail_of(after))]
        check(renewed["verdict"] == "RENEWED"
              and renewed["executed"] is True
              and tail_of(after) == tail_of(original)
              and '"declared_by": "R2351"' in head_region
              and '"declared_by": "R2331"' not in head_region
              and "renewed at R2351 by residue_triage_head_renew" in head_region
              and sized == planned["predicted_bytes"]
              == renewed["predicted_bytes"]
              and not residue
              and reread["declared_by"] == "R2351"
              and "DECLARED_BY" not in kinds
              and len(reread["breaks"]) == planned["remaining_breaks"]
              and reread["first_break"] == planned["remaining_first"],
              "AC-RTRH4 atomic splice")
        if tail_of(after) != tail_of(original):
            print("  measured: entries region moved", flush=True)
        if "DECLARED_BY" in kinds:
            print("  measured: reread=%r" % (reread,), flush=True)
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rtrh5():
    """CLI codes are pinned and --json is byte-stable in the pinned order."""
    planned = make_world()
    renewed = make_world()
    refused = make_world()
    missing = make_world(no_decl=True)
    unreadable = make_world(raw="{not json")
    try:
        code0, out0, _ = run_cli(["--round", "R2351"], world=planned)
        code0_json, out_json, _ = run_cli(["--round", "R2351", "--json"],
                                          world=planned)
        again, out_again, _ = run_cli(["--round", "R2351", "--json"],
                                      world=planned)
        code0_exe, out_exe, _ = run_cli(
            ["--round", "R2351", "--execute"], world=renewed)
        code2, out2, _ = run_cli(["--round", "R2340"], world=refused)
        code3, out3, _ = run_cli(["--round", "R2351"], world=missing)
        code3b, out3b, _ = run_cli(["--round", "R2351"], world=unreadable)
        code5, out5, _ = run_cli(["--nope"], world=planned)
        code5b, out5b, _ = run_cli([], world=planned)
        body = json.loads(out_json) if out_json.strip() else {}
        check(code0 == 0 and "PLANNED" in out0
              and code0_json == 0
              and tuple(body.keys()) == HR.REPORT_KEYS
              and body.get("verdict") == "PLANNED"
              and again == 0 and out_again == out_json
              and code0_exe == 0 and "RENEWED" in out_exe
              and code2 == 2 and "E_RTRH_HEAD_PREDATES" in out2
              and code3 == 3 and "E_RTRH_UNPINNED" in out3
              and code3b == 3 and "E_RTR_UNREADABLE" in out3b
              and code5 == 5 and "E_RTRH_BAD_ARGS" in out5
              and code5b == 5 and "E_RTRH_BAD_ARGS" in out5b,
              "AC-RTRH5 CLI codes")
        if tuple(body.keys()) != HR.REPORT_KEYS:
            print("  measured keys: %r" % (tuple(body.keys()),), flush=True)
    finally:
        for world in (planned, renewed, refused, missing, unreadable):
            shutil.rmtree(world, ignore_errors=True)


def ac_rtrh6():
    """Pure ASCII, stdlib only, no clock, no network, no delete, wired."""
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
        "test_residue_triage_head_renew.py" in runner
    check(ascii_ok
          and imports <= {"json", "os", "re", "sys", "residue_triage",
                          "residue_triage_decl_reason"}
          and not clean
          and wired,
          "AC-RTRH6 purity and wiring")
    if clean or not ascii_ok or not wired:
        print("  measured: ascii=%r clean=%r wired=%r imports=%r"
              % (ascii_ok, clean, wired, sorted(imports)), flush=True)


def main():
    for name in ("ac_rtrh1", "ac_rtrh2", "ac_rtrh3", "ac_rtrh4", "ac_rtrh5",
                 "ac_rtrh6"):
        globals()[name]()
    total = PASSES + FAILS
    verdict = "PASS" if FAILS == 0 and total == EXPECTED_CRITERIA else "FAIL"
    print("SUITE %s %d/%d" % (verdict, PASSES, total))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())