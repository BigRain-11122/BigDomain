"""matrix_evidence_pile_consistency suite (R2396; criteria AC-MEPC1..AC-MEPC6

were pre-registered inside the R2386 seed row of state/queue/tech.md BEFORE
this code existed).

What this proves: the string the matrix section hands its tool is derived from
the SAME pile the guard reads, so a bare evidence name is handed over as
`<measured pile>/<basename>` - and the old R2386 reading (which handed the bare
name to a tool that resolves it against the root) is closed rather than
described. A name that carries a directory is handed through byte for byte, and
a name that cannot be placed refuses before the tool is called at all.

Every world below is a stand-in root; the matrix tool is faked through the
injectable `call`, so no real matrix is ever rendered and the shipped tree is
never touched. Stdlib only, ASCII source, zero network. Exit 0 = all green.
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

import bare_evidence_pile_refusal as BEPR  # noqa: E402
import battery_followup as BF  # noqa: E402
import followup_section_foreign_wire as FSFW  # noqa: E402
import matrix_evidence_pile_consistency as MEPC  # noqa: E402
import matrix_stamp_compare as MSC  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "matrix_evidence_pile_consistency.py")
WIRE = os.path.join(BASE, "followup_section_foreign_wire.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-matrix-evidence-pile-consistency"
REPO_DOC = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")


def stamp_line():
    """R2418: a stand-in doc must carry a real stamp line, taken through the
    law rather than spelled here, because the matrix section now refuses a doc
    with none (E_MSC_NO_STAMP)."""
    verdict, _code, stamp, _detail = MSC.stamp_of(REPO_DOC)
    if verdict != MSC.PASS or not stamp:
        return None
    with io.open(REPO_DOC, "r", encoding="utf-8") as handle:
        for line in handle.read().split("\n"):
            if stamp in line:
                return line
    return None


STAMP_LINE = stamp_line()

DOC_BYTES = (("%s\nMATRIX\n" % STAMP_LINE)
             if STAMP_LINE else "MATRIX\n").encode("utf-8")
BARE = "reconcile-all-R9001.log"
VOCAB = ("matrix", "fingerprint", "profile", "census")

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


def write(path, text):
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def log_text(names, round_label="R9001"):
    lines = ["SECTION %s PASS detail" % name for name in names]
    lines.append("VERDICT %s PASS" % round_label)
    return "\n".join(lines) + "\n"


def make_world(piles=("qa",), bare=BARE):
    """A stand-in root: evidence piles, the matrix doc and the tool stub."""
    world = tempfile.mkdtemp(prefix="bigdomain-mepc-w-")
    write(os.path.join(world, "src", "sandbox", "suite_matrix.py"),
          "print('stub')\n")
    path = os.path.join(world, "docs", "sandbox-suite-matrix.md")
    if not os.path.isdir(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    with open(path, "wb") as handle:
        handle.write(DOC_BYTES)
    for pile in piles:
        write(os.path.join(world, pile, bare), log_text(VOCAB))
    return world


def drop_world(world):
    shutil.rmtree(world, ignore_errors=True)


def recording_call(body=DOC_BYTES):
    """A stand-in for the matrix tool that records every argv it is handed."""
    seen = []

    def call(cmd):
        seen.append(list(cmd))
        if "--out" in cmd:
            target = cmd[cmd.index("--out") + 1]
            with open(target, "wb") as handle:
                handle.write(body)
            return 0, "PASS generated matrix\n"
        return 0, "PASS check: byte-identical\n"

    call.seen = seen
    return call


def evidence_arg(cmd):
    return cmd[cmd.index("--evidence") + 1] if "--evidence" in cmd else None


def run_cli(args):
    proc = subprocess.run([sys.executable, MODULE] + args,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          cwd=REPO)
    return (proc.returncode,
            proc.stdout.decode("ascii", "replace"),
            proc.stderr.decode("ascii", "replace"))


def ac_mepc1():
    """A bare name is handed as pile+basename, and a patched pile moves it."""
    world = make_world(piles=("qa",))
    call = recording_call()
    FSFW.matrix_section(world, BARE, call)
    measured = evidence_arg(call.seen[0]) if call.seen else None
    placement = MEPC.placement(BARE, world)
    # The patched pile must exist for the guard to read it, but the bare name
    # may not live in two piles at once or the REAL measurement refuses as
    # ambiguous - so it is created only for the patched leg.
    write(os.path.join(world, "other", BARE), log_text(VOCAB))
    real = BEPR.pile_for
    try:
        BEPR.pile_for = lambda evidence, root: "other"
        moved_call = recording_call()
        FSFW.matrix_section(world, BARE, moved_call)
        moved = (evidence_arg(moved_call.seen[0])
                 if moved_call.seen else None)
        moved_placement = MEPC.placement(BARE, world)
    finally:
        BEPR.pile_for = real
    ok = (measured == os.path.join("qa", BARE)
          and moved == os.path.join("other", BARE)
          and placement["argument"] == os.path.join("qa", BARE)
          and moved_placement["argument"] == os.path.join("other", BARE)
          and measured != moved)
    if not ok:
        print("  measured: measured=%r moved=%r placement=%r"
              % (measured, moved, placement["argument"]))
    drop_world(world)
    check(ok, "AC-MEPC1 a bare evidence name reaches the tool as the measured "
              "pile plus the basename, and a patched derivation moves the "
              "argument the tool receives")


def ac_mepc2():
    """A name that carries a directory is handed through byte for byte."""
    world = make_world()
    named = "qa/" + BARE
    dotted = "./qa/" + BARE
    call = recording_call()
    entry, body = FSFW.matrix_section(world, named, call)
    expected_entry, expected_body = BF.matrix_core(world, named,
                                                   recording_call())
    ok = (MEPC.tool_argument(named, world) == named
          and MEPC.tool_argument(dotted, world) == dotted
          and evidence_arg(call.seen[0]) == named
          and entry == expected_entry and body == expected_body)
    if not ok:
        print("  measured: named=%r dotted=%r entry=%r expected=%r"
              % (MEPC.tool_argument(named, world),
                 MEPC.tool_argument(dotted, world), entry, expected_entry))
    drop_world(world)
    check(ok, "AC-MEPC2 a name that carries a directory is handed through "
              "unchanged, byte for byte, and its section report is the "
              "pre-wire reading")


def ac_mepc3():
    """Under a root that is not the cwd, both halves name the SAME file."""
    world = make_world(piles=("qa",))
    placement = MEPC.placement(BARE, world)
    argument = placement["argument"]
    tool_side = os.path.normpath(os.path.join(world, argument))
    guard_side = os.path.normpath(os.path.join(world, placement["pile"],
                                               os.path.basename(BARE)))
    call = recording_call()
    FSFW.matrix_section(world, BARE, call)
    section_arg = evidence_arg(call.seen[0]) if call.seen else None
    # The R2386 defect measured against this very world: the bare name the
    # section used to hand over does not exist under the root at all.
    old_side = os.path.normpath(os.path.join(world, BARE))
    ok = (placement["same_file"] is True
          and tool_side == guard_side
          and os.path.isfile(tool_side)
          and not os.path.isfile(old_side)
          and section_arg == argument
          and os.path.dirname(argument) == placement["pile"])
    if not ok:
        print("  measured: argument=%r same=%r tool=%r guard=%r old=%r"
              % (argument, placement["same_file"], tool_side, guard_side,
                 old_side))
    drop_world(world)
    check(ok, "AC-MEPC3 the tool argument and the guarded pile resolve to the "
              "same file under a root that is not the cwd - the old bare name "
              "resolved to nothing there")


def ac_mepc4():
    """A name that cannot be placed refuses before the tool is called."""
    nowhere = make_world(piles=("qa",))
    missing_call = recording_call()
    missing_entry, missing_body = FSFW.matrix_section(
        nowhere, "no-such-log-R9002.log", missing_call)
    twice = make_world(piles=("qa", "lab"))
    twice_call = recording_call()
    twice_entry, twice_body = FSFW.matrix_section(twice, BARE, twice_call)
    empty = MEPC.placement("", nowhere)
    ok = (missing_entry["verdict"] == "FAIL"
          and MEPC.E_MEPC_UNPLACEABLE in missing_entry["detail"]
          and BEPR.E_BEPR_NOT_FOUND in missing_entry["detail"]
          and missing_body == "" and missing_call.seen == []
          and twice_entry["verdict"] == "FAIL"
          and BEPR.E_BEPR_AMBIGUOUS in twice_entry["detail"]
          and twice_body == "" and twice_call.seen == []
          and empty["verdict"] == MEPC.REFUSED
          and empty["code"] == MEPC.E_MEPC_BAD_EVIDENCE)
    if not ok:
        print("  measured: missing=%r body=%r calls=%r twice=%r calls2=%r "
              "empty=%r"
              % (missing_entry, missing_body, missing_call.seen, twice_entry,
                 twice_call.seen, empty["code"]))
    drop_world(nowhere)
    drop_world(twice)
    check(ok, "AC-MEPC4 a name that cannot be placed refuses before the tool "
              "is called at all, so no doc is rendered from a pile the guard "
              "cannot name")


def ac_mepc5():
    """CLI codes 0/2/3/5 and a byte-stable --json over the pinned keys."""
    world = make_world(piles=("qa",))
    write(os.path.join(world, "void", "notes.log"), "no evidence here\n")
    rc_placed, out_placed, _ = run_cli(["--check", BARE, "--root", world])
    rc_missing, out_missing, _ = run_cli(
        ["--check", "absent-R9005.log", "--root", world])
    rc_unreadable, _, _ = run_cli(
        ["--check", "notes.log", "--root", world])
    rc_bad, _, _ = run_cli(["--nope"])
    rc_j1, json_one, _ = run_cli(["--check", BARE, "--root", world, "--json"])
    rc_j2, json_two, _ = run_cli(["--check", BARE, "--root", world, "--json"])
    try:
        keys = list(json.loads(json_one).keys())
    except ValueError:
        keys = []
    named = "qa/" + BARE
    entry, body = FSFW.matrix_section(world, named, recording_call())
    expected_entry, expected_body = BF.matrix_core(world, named,
                                                   recording_call())
    ok = (rc_placed == 0 and rc_missing == 2 and rc_unreadable == 3
          and rc_bad == 5
          and "argument=%s" % os.path.join("qa", BARE) in out_placed
          and "same_file=yes" in out_placed
          and BEPR.E_BEPR_NOT_FOUND in out_missing
          and rc_j1 == 0 and rc_j2 == 0 and json_one == json_two
          and tuple(keys) == MEPC.JSON_KEYS
          and entry == expected_entry and body == expected_body)
    if not ok:
        print("  measured: rc=%r/%r/%r/%r json_equal=%r keys=%r entry=%r"
              % (rc_placed, rc_missing, rc_unreadable, rc_bad,
                 json_one == json_two, keys, entry))
    drop_world(world)
    check(ok, "AC-MEPC5 the section report for an unchanged pile stays "
              "byte-identical to the R2386 reading and the CLI codes 0/2/3/5 "
              "with a byte-stable --json over the pinned keys are unchanged")


def ac_mepc6():
    """Pure ASCII stdlib, no clock/network, asked at call time, wired."""
    with open(MODULE, "rb") as handle:
        raw = handle.read()
    try:
        text = raw.decode("ascii")
        ascii_ok = True
    except UnicodeDecodeError:
        text = raw.decode("ascii", "replace")
        ascii_ok = False
    banned = ("socket", "urllib", "requests", "http.client", "time.time",
              "datetime", "import time")
    pure = not any(token in text for token in banned)
    stdlib_only = "import json\nimport os\nimport sys\n" in text
    sibling_at_call = ("\nimport bare_evidence_pile_refusal as BEPR"
                       not in text
                       and "import followup_guard_evidence_scope as FGES"
                       in text
                       and "import bare_evidence_pile_refusal as BEPR"
                       in text)
    with open(WIRE, "rb") as handle:
        wire_text = handle.read().decode("ascii", "replace")
    start = wire_text.find("def matrix_section")
    end = wire_text.find("def render")
    section = wire_text[start:end] if start >= 0 and end > start else ""
    wire_asks = ("import matrix_evidence_pile_consistency as MEPC" in section
                 and "MEPC.align(evidence, root, directory)" in section)
    with open(RUNNER, "rb") as handle:
        runner_text = handle.read().decode("ascii", "replace")
    wired = LABEL in runner_text
    ok = (ascii_ok and pure and stdlib_only and sibling_at_call
          and wire_asks and wired)
    if not ok:
        print("  measured: ascii=%r pure=%r stdlib=%r call=%r asked=%r "
              "wired=%r"
              % (ascii_ok, pure, stdlib_only, sibling_at_call, wire_asks,
                 wired))
    check(ok, "AC-MEPC6 pure ASCII, stdlib only, zero network, no clock, the "
              "sibling laws imported at call time, asked by the matrix "
              "section, plus its own reconcile label")


def main():
    print("matrix_evidence_pile_consistency suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_mepc1()
    ac_mepc2()
    ac_mepc3()
    ac_mepc4()
    ac_mepc5()
    ac_mepc6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())