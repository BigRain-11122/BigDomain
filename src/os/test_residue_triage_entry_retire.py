"""residue_triage_entry_retire suite (R2353; criteria AC-RTER1..AC-RTER6 were
pre-registered inside the R2351 seed row of state/queue/tech.md BEFORE this
code existed).

What this proves: an entry whose round left the live residue can finally be
removed by a writer that only removes what the live reading proves is gone.
The entry set is read by residue_triage own loader and the live residue by its
own live reading (patching either moves the plan, and this module carries no
second declaration reader), the dry run is the default and writes no byte, a
round the live reading still carries is refused with its round named, the
executed retire is one atomic splice that leaves every surviving entry and the
head byte-identical and proves its own predicted size with no temp residue,
the CLI codes are pinned with a byte-stable --json, and the module is pure
ASCII, stdlib only, reads no clock, touches no network and holds exactly one
delete call - the cleanup of its own temp file.

The fixtures deliberately carry BOTH live entry layouts (a compact one-line
object and an expanded block), because the splice is span based: re-rendering
an entry to find it would miss half the real file.

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
import residue_triage_entry_retire as ER  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "residue_triage_entry_retire.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-residue-triage-entry-retire"

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


def declaration_text(head="R2331", reason="renewed at R2331 for the suite"):
    """The pinned shape in BOTH live layouts: compact first, expanded last."""
    return (
        '{\n'
        '  "declared_by": "%s",\n'
        '  "reason": "%s",\n'
        '  "entries": [\n'
        '    {"round": 2300, "status": "DELIVERED", "declared_by": "R2331",'
        ' "reason": "compact layout", "until": 2350},\n'
        '    {"round": 2305, "status": "DELIVERED", "declared_by": "R2331",'
        ' "reason": "compact layout", "until": 2350},\n'
        '    {\n'
        '      "round": 2400,\n'
        '      "status": "DELIVERED",\n'
        '      "declared_by": "R2342",\n'
        '      "reason": "this round left the live residue and is unmatched",\n'
        '      "until": 2350\n'
        '    }\n'
        '  ]\n'
        '}\n' % (head, reason))


def declaration_text_lead_unmatched():
    """The same three entries with the unmatched one FIRST (expanded block)."""
    return (
        '{\n'
        '  "declared_by": "R2331",\n'
        '  "reason": "renewed at R2331 for the suite",\n'
        '  "entries": [\n'
        '    {\n'
        '      "round": 2400,\n'
        '      "status": "DELIVERED",\n'
        '      "declared_by": "R2342",\n'
        '      "reason": "this round left the live residue and is unmatched",\n'
        '      "until": 2350\n'
        '    },\n'
        '    {"round": 2300, "status": "DELIVERED", "declared_by": "R2331",'
        ' "reason": "compact layout", "until": 2350},\n'
        '    {"round": 2305, "status": "DELIVERED", "declared_by": "R2331",'
        ' "reason": "compact layout", "until": 2350}\n'
        '  ]\n'
        '}\n')


def tech_rows(rounds=("R2300", "R2305")):
    return "".join("- [x] [done 2026-11-01 %s] a closed residue row\n" % value
                   for value in rounds)


def make_world(raw=None, no_decl=False, live_rounds=("R2300", "R2305")):
    """A throwaway root: state.json, the three queues, the declaration."""
    world = tempfile.mkdtemp(prefix="rter-world-")
    os.makedirs(os.path.join(world, "state", "queue"))
    os.makedirs(os.path.join(world, "src", "os"))
    payload = {"tick": 2300, "log": ["R2200 a logged item"]}
    path = os.path.join(world, "src", "os", "state.json")
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload))
    bodies = {"tech": tech_rows(live_rounds), "main": HEADER,
              "explore": HEADER}
    for name in bodies:
        path = os.path.join(world, "state", "queue", name + ".md")
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(bodies[name])
    if no_decl:
        return world
    path = os.path.join(world, "state", "residue_triage.json")
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(raw if raw is not None else declaration_text())
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


def head_region(text):
    """Everything before the entries array, byte for byte."""
    return text[:text.find('"entries"')]


def blocks(text):
    """Every entry object block as raw text, located by span, not rendering."""
    spans = ER._spans(text)
    return [text[start:end] for start, end in spans]


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
    except ER.EntryRetireError as exc:
        return exc.code, exc.detail
    except Exception as exc:  # noqa: BLE001 - a wrong error is not a refusal
        return "WRONG:" + type(exc).__name__, ""
    return None, ""


def code_only(text):
    """The source with comments and docstrings removed (call scans only)."""
    without_docstrings = re.sub(r'"""(?:.|\n)*?"""', '', text)
    without_docstrings = re.sub(r"'''(?:.|\n)*?'''", '', without_docstrings)
    return re.sub(r"#[^\n]*", "", without_docstrings)


def ac_rter1():
    """The entry set and the live residue are imported, never re-derived."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    code = code_only(source)
    no_second_reader = ("import residue_triage as RT" in code
                        and "json.loads" not in code
                        and "def load_declaration" not in code
                        and "residue_triage.json" not in code
                        and ER.DECLARATION_PATH == RT.DECLARATION_PATH)

    world = make_world()
    # a patched loader moves the unmatched list the plan names
    synthetic = {"declared_by": 2331, "reason": "synthetic",
                 "entries": [
                     {"round": 2300, "status": "DELIVERED",
                      "declared_by": 2331, "reason": "synthetic",
                      "until": 2350},
                     {"round": 2401, "status": "DELIVERED",
                      "declared_by": 2331, "reason": "synthetic",
                      "until": 2350},
                     {"round": 2400, "status": "DELIVERED",
                      "declared_by": 2342, "reason": "synthetic",
                      "until": 2350},
                 ]}
    saved_loader = RT.load_declaration
    RT.load_declaration = lambda root: synthetic

    def fake_read(path):
        return None

    try:
        patched = ER.plan(world, "R2400")
    finally:
        RT.load_declaration = saved_loader

    # a patched live reading moves the refusal: 2400 becomes live
    saved_live = RT.live_residue
    RT.live_residue = lambda root: [
        {"round": 2300, "status": "DELIVERED"},
        {"round": 2305, "status": "DELIVERED"},
        {"round": 2400, "status": "DELIVERED"},
    ]
    try:
        moved = refuse(ER.plan, world, "R2400")
    finally:
        RT.live_residue = saved_live

    plain = ER.plan(world, "R2400")
    shutil.rmtree(world, ignore_errors=True)
    ok = (no_second_reader
          and patched["unmatched"] == [2401, 2400]
          and moved[0] == "E_RTER_LIVE" and "R2400" in moved[1]
          and plain["unmatched"] == [2400])
    if not ok:
        print("  measured: import=%r patched=%r moved=%r plain=%r"
              % (no_second_reader, patched.get("unmatched"), moved[0],
                 plain.get("unmatched")), flush=True)
    check(ok, "AC-RTER1 imports")


def ac_rter2():
    """The dry run is the default: it plans by number and writes no byte."""
    world = make_world()
    try:
        before = file_map(world)
        planned = ER.plan(world, "R2400")
        after = file_map(world)
        item = ER.report(planned)
        execute_world = make_world()
        try:
            executed = ER.plan(execute_world, "R2400", True)
            written = os.path.getsize(
                os.path.join(execute_world, "state", "residue_triage.json"))
        finally:
            shutil.rmtree(execute_world, ignore_errors=True)
        ok = (item["verdict"] == "PLANNED"
              and item["wrote"] is False
              and item["round"] == "R2400"
              and item["unmatched"] == ["R2400"]
              and item["entries_before"] == 3
              and item["entries_after"] == 2
              and item["delta"] < 0
              and item["after_bytes"] == planned["before_bytes"] + item["delta"]
              and item["after_bytes"] == executed["before_bytes"]
              + executed["delta"]
              and written == item["after_bytes"]
              and before == after)
        if not ok:
            print("  measured: %r written=%r" % (item, written), flush=True)
        check(ok, "AC-RTER2 dry run plans and writes nothing")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rter3():
    """A live round refuses with its round named; the tree stays untouched."""
    live_world = make_world()
    absent_world = make_world()
    outcomes = []
    trees = []
    for world, round_text in ((live_world, "R2300"), (absent_world, "R2500")):
        before = file_map(world)
        outcomes.append(refuse(ER.plan, world, round_text, True))
        trees.append(before == file_map(world))
    for world in (live_world, absent_world):
        shutil.rmtree(world, ignore_errors=True)
    codes = [item[0] for item in outcomes]
    ok = (codes == ["E_RTER_LIVE", "E_RTER_NOT_DECLARED"]
          and "R2300" in outcomes[0][1]
          and "R2500" in outcomes[1][1]
          and all(trees))
    if not ok:
        print("  measured: %r trees=%r" % (outcomes, trees), flush=True)
    check(ok, "AC-RTER3 refusals name their rounds")


def ac_rter4():
    """One atomic splice: survivors and head byte-identical, size proved."""
    world = make_world()
    try:
        path = os.path.join(world, "state", "residue_triage.json")
        original = io.open(path, "r", encoding="utf-8").read()
        planned = ER.plan(world, "R2400")
        executed = ER.plan(world, "R2400", True)
        after = io.open(path, "r", encoding="utf-8").read()
        sized = os.path.getsize(path)
        leftovers = [name for name in os.listdir(os.path.dirname(path))
                     if name.endswith(".tmp-rter") or name.endswith(".part")]
        reread = RT.load_declaration(world)
        before_blocks = blocks(original)
        after_blocks = blocks(after)
        # the LAST entry is the one retired: the two compact blocks must
        # survive byte for byte, in order, and the head must not move
        ok = (executed["executed"] is True
              and ER.report(executed)["verdict"] == "RETIRED"
              and head_region(after) == head_region(original)
              and after_blocks == before_blocks[:2]
              and [entry["round"] for entry in reread["entries"]]
              == [2300, 2305]
              and sized == planned["before_bytes"] + planned["delta"]
              == ER.report(planned)["after_bytes"]
              and not leftovers)
        # the FIRST entry retires by cutting the FORWARD separator instead
        first_world = make_world(raw=declaration_text_lead_unmatched())
        try:
            first_path = os.path.join(first_world, "state",
                                      "residue_triage.json")
            first_before = io.open(first_path, "r", encoding="utf-8").read()
            first_plan = ER.plan(first_world, "R2400")
            ER.plan(first_world, "R2400", True)
            first_after = io.open(first_path, "r", encoding="utf-8").read()
            first_reread = RT.load_declaration(first_world)
            ok = (ok
                  and first_after != first_before
                  and [entry["round"] for entry in first_reread["entries"]]
                  == [2300, 2305]
                  and blocks(first_after) == blocks(first_before)[1:]
                  and head_region(first_after) == head_region(first_before)
                  and os.path.getsize(first_path)
                  == ER.report(first_plan)["after_bytes"])
        finally:
            shutil.rmtree(first_world, ignore_errors=True)
        if not ok:
            print("  measured: blocks=%r reread=%r leftovers=%r"
                  % (len(after_blocks),
                     [item["round"] for item in reread["entries"]],
                     leftovers), flush=True)
        check(ok, "AC-RTER4 atomic splice")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rter5():
    """CLI codes are pinned and --json is byte-stable in the pinned order."""
    planned = make_world()
    retired = make_world()
    live = make_world()
    missing = make_world(no_decl=True)
    unreadable = make_world(raw="{not json")
    try:
        code0, out0, _ = run_cli(["--round", "R2400"], world=planned)
        code0_json, out_json, _ = run_cli(["--round", "R2400", "--json"],
                                          world=planned)
        again, out_again, _ = run_cli(["--round", "R2400", "--json"],
                                      world=planned)
        code0_exe, out_exe, _ = run_cli(["--round", "R2400", "--execute"],
                                        world=retired)
        code2, out2, _ = run_cli(["--round", "R2300"], world=live)
        code2b, out2b, _ = run_cli(["--round", "R2500"], world=live)
        code3, out3, _ = run_cli(["--round", "R2400"], world=missing)
        code3b, out3b, _ = run_cli(["--round", "R2400"], world=unreadable)
        code5, out5, _ = run_cli(["--nope"], world=planned)
        code5b, out5b, _ = run_cli([], world=planned)
        body = json.loads(out_json) if out_json.strip() else {}
        ok = (code0 == 0 and "PLANNED" in out0
              and code0_json == 0
              and tuple(body.keys()) == ER.REPORT_KEYS
              and body.get("verdict") == "PLANNED"
              and body.get("unmatched") == ["R2400"]
              and again == 0 and out_again == out_json
              and code0_exe == 0 and "RETIRED" in out_exe
              and code2 == 2 and "E_RTER_LIVE" in out2
              and code2b == 2 and "E_RTER_NOT_DECLARED" in out2b
              and code3 == 3 and "E_RTER_UNPINNED" in out3
              and code3b == 3 and "E_RTR_UNREADABLE" in out3b
              and code5 == 5 and "E_RTER_BAD_ARGS" in out5
              and code5b == 5 and "E_RTER_BAD_ARGS" in out5b)
        if not ok:
            print("  measured: keys=%r codes=%r"
                  % (tuple(body.keys()), [code0, code0_exe, code2, code2b,
                                          code3, code3b, code5, code5b]),
                  flush=True)
        check(ok, "AC-RTER5 CLI codes")
    finally:
        for world in (planned, retired, live, missing, unreadable):
            shutil.rmtree(world, ignore_errors=True)


def ac_rter6():
    """Pure ASCII, stdlib only, no clock, no network, one delete, wired."""
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
                 "unlink", "rmtree", "shutil", "os.system", "subprocess")
    clean = [token for token in forbidden if token in code]
    deletes = code.count("os.remove")
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('("%s"' % LABEL) in runner and \
        "test_residue_triage_entry_retire.py" in runner
    ok = (ascii_ok
          and imports <= {"json", "os", "sys", "residue_triage"}
          and not clean
          and deletes == 1
          and "atomic" in text.lower()
          and wired)
    if not ok:
        print("  measured: ascii=%r clean=%r deletes=%r wired=%r imports=%r"
              % (ascii_ok, clean, deletes, wired, sorted(imports)),
              flush=True)
    check(ok, "AC-RTER6 purity and wiring")


def main():
    for name in ("ac_rter1", "ac_rter2", "ac_rter3", "ac_rter4", "ac_rter5",
                 "ac_rter6"):
        globals()[name]()
    total = PASSES + FAILS
    verdict = "PASS" if FAILS == 0 and total == EXPECTED_CRITERIA else "FAIL"
    print("SUITE %s %d/%d" % (verdict, PASSES, total))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())