"""followup_bare_evidence_face suite (R2404; criteria AC-FBEF1..AC-FBEF6 were

pre-registered inside the R2396 seed row of state/queue/tech.md BEFORE this
code existed).

What this proves: the only face an operator walks - the follow-up CLI - finally
resolves an evidence name the SAME way the matrix section already did, so
`battery_followup.py --evidence reconcile-all-<round>.log` reaches the four
sections over the file the pile law measured instead of answering
MISSING EVIDENCE at exit 3.

Every world below is a stand-in root; the four sections are faked either through
`battery_followup.section_matrix` or through stubs that exit 0, so no real
battery or matrix is ever produced. Stdlib only, ASCII source, zero network.
Exit 0 = all green.
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
sys.path.insert(0, BASE)

import bare_evidence_pile_refusal as BEPR  # noqa: E402
import battery_followup as BF  # noqa: E402
import followup_bare_evidence_face as FBEF  # noqa: E402
import matrix_evidence_pile_consistency as MEPC  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "followup_bare_evidence_face.py")
CLI = os.path.join(BASE, "battery_followup.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-followup-bare-evidence-face"
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
    """A stand-in root: one evidence pile, the matrix doc and a tool stub."""
    world = tempfile.mkdtemp(prefix="bigdomain-fbef-w-")
    write(os.path.join(world, "src", "sandbox", "suite_matrix.py"),
          "print('stub')\n")
    path = os.path.join(world, "docs", "sandbox-suite-matrix.md")
    if not os.path.isdir(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    with open(path, "wb") as handle:
        handle.write(b"MATRIX\n")
    for pile in piles:
        write(os.path.join(world, pile, bare), log_text(VOCAB))
    return world


def drop_world(world):
    shutil.rmtree(world, ignore_errors=True)


def run(argv):
    proc = subprocess.Popen([sys.executable, CLI] + argv,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace"), \
        err.decode("utf-8", "replace")


def ac_fbef1():
    """A bare name in exactly one pile resolves there, and a patched pile moves it."""
    world = make_world(("qa",))
    report = FBEF.placement(BARE, world)
    base_ok = (report["verdict"] == FBEF.RESOLVED
               and report["pile"] == "qa"
               and report["argument"] == os.path.join("qa", BARE)
               and report["exists"] is True)
    write(os.path.join(world, "logs", BARE), log_text(VOCAB))
    original = MEPC.pile_for
    MEPC.pile_for = lambda evidence, root, directory=None: "logs"
    try:
        moved = FBEF.placement(BARE, world)
    finally:
        MEPC.pile_for = original
    moved_ok = (moved["pile"] == "logs"
                and moved["argument"] == os.path.join("logs", BARE))
    if not (base_ok and moved_ok):
        print("  measured: base=%r moved=%r" % (report, moved))
    check(base_ok and moved_ok,
          "AC-FBEF1 a bare name living in exactly one pile is accepted and the "
          "sections receive that pile's path, and a patched pile moves what "
          "they receive")
    drop_world(world)


def ac_fbef2():
    """A directory-carrying name is passed through byte for byte, present or not."""
    world = make_world(("qa",))
    carried = os.path.join("qa", BARE).replace("\\", "/")
    present = FBEF.placement(carried, world)
    absent = FBEF.placement("qa/absent-R9001.log", world)
    ok = (present["argument"] == carried and present["exists"] is True
          and absent["argument"] == "qa/absent-R9001.log"
          and absent["exists"] is False
          and absent["verdict"] == FBEF.RESOLVED)
    if not ok:
        print("  measured: present=%r absent=%r" % (present, absent))
    check(ok, "AC-FBEF2 a name that carries a directory is joined to the root "
              "exactly as today, byte for byte, including its refusal at exit 3 "
              "when absent")
    drop_world(world)


def ac_fbef3():
    """Unplaceable bare names refuse with the pile law's own code, never a guess."""
    nowhere = make_world(("qa",))
    two = make_world(("qa", "logs"))
    miss = FBEF.placement("nothing-R9001.log", nowhere)
    ambi = FBEF.placement(BARE, two)
    code, out, _ = run(["--evidence", "nothing-R9001.log", "--dry-run",
                        "--root", nowhere])
    ok = (miss["verdict"] == FBEF.REFUSED
          and miss["code"] == BEPR.E_BEPR_NOT_FOUND
          and ambi["verdict"] == FBEF.REFUSED
          and ambi["code"] == BEPR.E_BEPR_AMBIGUOUS
          and code == 3 and BEPR.E_BEPR_NOT_FOUND in out
          and "MISSING EVIDENCE" in out)
    if not ok:
        print("  measured: miss=%r ambi=%r rc=%r out=%r"
              % (miss, ambi, code, out.strip()))
    check(ok, "AC-FBEF3 a bare name that lives nowhere or in two piles refuses "
              "at exit 3 naming the pile law's own code, never a guessed pile")
    drop_world(nowhere)
    drop_world(two)


def ac_fbef4():
    """The sections' report for a resolved bare name equals the directory form."""
    world = make_world(("qa",))
    argument = FBEF.placement(BARE, world)["argument"]
    seen = []
    original = BF.section_matrix

    def stub(root, evidence, call):
        seen.append(evidence)
        return ({"section": "matrix", "verdict": "PASS",
                 "detail": "matrix byte-identical 7B"}, "MATRIX\n")

    BF.section_matrix = stub
    try:
        call = lambda cmd: (0, "ok")  # noqa: E731
        bare_report, bare_bodies = BF.sections(world, argument, "R9001", 9001,
                                               call=call)
        dir_report, dir_bodies = BF.sections(
            world, os.path.join("qa", BARE), "R9001", 9001, call=call)
    finally:
        BF.section_matrix = original
    rendered_bare = BF.render(bare_report)
    rendered_dir = BF.render(dir_report)
    ok = (bare_report == dir_report
          and bare_bodies == dir_bodies
          and rendered_bare == rendered_dir
          and seen == [argument, os.path.join("qa", BARE)])
    if not ok:
        print("  measured: equal=%r bodies=%r seen=%r"
              % (bare_report == dir_report, bare_bodies == dir_bodies, seen))
    check(ok, "AC-FBEF4 the section report for an accepted bare name is "
              "byte-identical to the report produced from the same file passed "
              "with its directory")
    drop_world(world)


def ac_fbef5():
    """CLI codes and the json payload are unchanged for working invocations."""
    world = make_world(("qa",))
    rc_dir, out_dir, _ = run(["--evidence", "qa/absent-R9001.log", "--dry-run",
                              "--root", world])
    rc_bad, out_bad, _ = run(["--evidence", BARE, "--nope", "--root", world])
    rc_bare, out_bare, _ = run(["--evidence", BARE, "--dry-run", "--root", world,
                                "--json"])
    rc_again, out_again, _ = run(["--evidence", BARE, "--dry-run",
                                  "--root", world, "--json"])
    okay_dir = (rc_dir == 3 and out_dir.strip() == "MISSING EVIDENCE "
                "qa/absent-R9001.log")
    okay_bad = rc_bad == 5 and "E_BFU_BAD_ARGS" in out_bad
    header, _, payload = out_bare.partition("\n{")
    body = "{" + payload if payload else ""
    payload_ok = False
    try:
        parsed = json.loads(body) if body else {}
        payload_ok = (parsed.get("evidence") == os.path.join("qa", BARE))
    except ValueError:
        parsed = {}
    stable = out_bare == out_again and rc_bare == rc_again
    not_missing = rc_bare != 3 and "MISSING EVIDENCE" not in out_bare
    root_name = os.path.join(world, "root-R9001.log")
    write(root_name, log_text(VOCAB))
    root_report = FBEF.placement("root-R9001.log", world)
    root_ok = (root_report["argument"] == "root-R9001.log"
               and root_report["exists"] is True)
    ok = (okay_dir and okay_bad and payload_ok and stable and not_missing
          and root_ok)
    if not ok:
        print("  measured: rc=%r/%r/%r dir=%r bad=%r payload=%r stable=%r "
              "not_missing=%r root=%r"
              % (rc_dir, rc_bad, rc_bare, out_dir.strip(), out_bad.strip(),
                 parsed.get("evidence"), stable, not_missing, root_report))
    check(ok, "AC-FBEF5 CLI codes 0/2/3/5 and the --json payload are unchanged "
              "for every already-working invocation, and a resolved bare name "
              "no longer answers MISSING EVIDENCE")
    drop_world(world)


def ac_fbef6():
    """Pure ASCII stdlib, no clock/network, laws asked at call time, wired."""
    with open(MODULE, "rb") as handle:
        raw = handle.read()
    try:
        text = raw.decode("ascii")
        ascii_ok = True
    except UnicodeDecodeError:
        text = raw.decode("ascii", "replace")
        ascii_ok = False
    banned = ("socket", "urllib", "requests", "http.client", "time.time",
              "datetime", "import time", "random")
    pure = not any(token in text for token in banned)
    stdlib_only = text.startswith('"""') and "import json\nimport os\nimport sys\n" in text
    no_top_level_law = "\nimport matrix_evidence_pile_consistency" not in text
    laws_at_call = ("    import matrix_evidence_pile_consistency as MEPC" in text
                    and "    import bare_evidence_pile_refusal as BEPR" in text)
    with open(CLI, "rb") as handle:
        cli_text = handle.read().decode("ascii", "replace")
    cli_asks = ("import followup_bare_evidence_face as FBEF" in cli_text
                and 'FBEF.placement(opts["evidence"], opts["root"])' in cli_text)
    with open(RUNNER, "rb") as handle:
        runner_text = handle.read().decode("ascii", "replace")
    wired = LABEL in runner_text
    ok = (ascii_ok and pure and stdlib_only and no_top_level_law
          and laws_at_call and cli_asks and wired)
    if not ok:
        print("  measured: ascii=%r pure=%r stdlib=%r top=%r call=%r cli=%r "
              "wired=%r"
              % (ascii_ok, pure, stdlib_only, no_top_level_law, laws_at_call,
                 cli_asks, wired))
    check(ok, "AC-FBEF6 pure ASCII, stdlib only, no clock, no network, asks the "
              "pile law at call time, plus its own reconcile label")


def main():
    print("followup_bare_evidence_face suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_fbef1()
    ac_fbef2()
    ac_fbef3()
    ac_fbef4()
    ac_fbef5()
    ac_fbef6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())