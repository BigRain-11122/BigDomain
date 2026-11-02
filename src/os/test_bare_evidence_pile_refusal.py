"""bare_evidence_pile_refusal suite (R2386; criteria AC-BEPR1..AC-BEPR6 were

pre-registered inside the R2380 seed row of state/queue/tech.md BEFORE this
code existed).

What this proves: a bare evidence filename is resolved to the pile the file
ACTUALLY lives in instead of falling back to a constant, a file living in a
FOREIGN-SECTION pile refuses while NAMING that pile, a file that lives nowhere
refuses with its own code, and a path that carries a directory keeps the R2380
reading byte for byte.

Every world below is a stand-in root; nothing under the shipped tree is
written. Stdlib only, ASCII source, zero network. Exit 0 = all green.
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
import followup_guard_evidence_scope as FGES  # noqa: E402
import followup_section_foreign as FSF  # noqa: E402
import followup_section_foreign_wire as FSFW  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "bare_evidence_pile_refusal.py")
WIRE = os.path.join(BASE, "followup_section_foreign_wire.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-bare-evidence-pile-refusal"
FOREIGN_NAME = "FOREIGN_RITUAL"
VOCAB = ("matrix", "fingerprint", "profile", "census")
BARE = "reconcile-all-R9001.log"

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


def make_world(clean_piles=("qa",), foreign_piles=(), bare=BARE,
               foreign_bare=None):
    """A stand-in root with clean and foreign evidence piles."""
    world = tempfile.mkdtemp(prefix="bigdomain-bepr-w-")
    for pile in clean_piles:
        write(os.path.join(world, pile, bare), log_text(VOCAB))
    for pile in foreign_piles:
        write(os.path.join(world, pile, foreign_bare or bare),
              log_text((FOREIGN_NAME,)))
    return world


def drop_world(world):
    shutil.rmtree(world, ignore_errors=True)


def run_cli(args):
    proc = subprocess.run([sys.executable, MODULE] + args,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          cwd=REPO)
    return (proc.returncode,
            proc.stdout.decode("ascii", "replace"),
            proc.stderr.decode("ascii", "replace"))


def ac_bepr1():
    """A bare filename is measured, and a patched resolver moves the pile."""
    world = make_world(clean_piles=("qa",), foreign_piles=("other",),
                       foreign_bare="reconcile-all-R9002.log")
    measured = BEPR.reading(BARE, world)
    real = BEPR.resolve_bare
    try:
        BEPR.resolve_bare = lambda evidence, root: "other"
        moved = BEPR.reading(BARE, world)
    finally:
        BEPR.resolve_bare = real
    with open(MODULE, "rb") as handle:
        text = handle.read().decode("ascii", "replace")
    start = text.find("def pile_for")
    end = text.find("def reading")
    slice_text = text[start:end] if start >= 0 and end > start else ""
    asked = "resolve_bare(evidence, root)" in slice_text
    no_default = ('"qa"' not in slice_text and "'qa'" not in slice_text
                  and "DEFAULT_DIR" not in slice_text)
    ok = (measured["dir"] == "qa"
          and measured["verdict"] == FSF.VERDICT_CLEAN
          and moved["dir"] == "other"
          and moved["verdict"] == FSF.VERDICT_FOREIGN
          and "dir=other" in BEPR.render(moved)
          and asked and no_default)
    if not ok:
        print("  measured: %r moved=%r asked=%r default=%r"
              % (measured["dir"], moved["dir"], asked, no_default))
    drop_world(world)
    check(ok, "AC-BEPR1 a bare filename derives its pile by STAT-ing it under "
              "the root and a patched resolver moves which pile is read")


def ac_bepr2():
    """An evidence path under qa keeps today's derived answer byte for byte."""
    world = make_world(clean_piles=("qa",))
    named = os.path.join("qa", BARE).replace(os.sep, "/")
    report = BEPR.reading(named, world)
    wire = FSFW.guard(world, "qa")
    projection = dict((key, report[key]) for key in FSFW.GUARD_KEYS)
    derived = FGES.evidence_dir(named)
    ok = (derived == "qa"
          and projection == wire
          and report["dir"] == "qa")
    if not ok:
        print("  measured: derived=%r projection=%r wire=%r"
              % (derived, projection, wire))
    drop_world(world)
    check(ok, "AC-BEPR2 an evidence path that carries a directory keeps the "
              "R2380 derived answer and the wire reading byte for byte")


def ac_bepr3():
    """A bare name living in a FOREIGN-SECTION pile refuses NAMING that pile."""
    world = make_world(clean_piles=(), foreign_piles=("elsewhere",))
    report = BEPR.reading(BARE, world)
    rc, out, _ = run_cli(["--check", BARE, "--root", world])
    entry, body = FSFW.matrix_section(world, BARE, lambda cmd: (0, ""))
    ok = (report["dir"] == "elsewhere"
          and report["verdict"] == FSF.VERDICT_FOREIGN
          and rc == 2
          and "dir=elsewhere" in out
          and entry["verdict"] == "FAIL"
          and FSFW.E_FSFW_FOREIGN_SECTION in entry["detail"]
          and body == ""
          and BEPR.exit_code(report) == 2)
    if not ok:
        print("  measured: dir=%r verdict=%r rc=%r out=%r entry=%r"
              % (report["dir"], report["verdict"], rc, out, entry))
    drop_world(world)
    check(ok, "AC-BEPR3 a bare filename that lives in a FOREIGN-SECTION pile "
              "refuses and names that pile, so the answer was measured")


def ac_bepr4():
    """A bare name that lives nowhere (or twice) refuses with its own code."""
    nowhere = make_world(clean_piles=("qa",))
    missing = BEPR.reading("no-such-log-R9002.log", nowhere)
    rc_missing, out_missing, _ = run_cli(
        ["--check", "no-such-log-R9002.log", "--root", nowhere])
    twice = make_world(clean_piles=("qa", "lab"))
    ambiguous = BEPR.reading(BARE, twice)
    rc_twice, out_twice, _ = run_cli(["--check", BARE, "--root", twice])
    ok = (missing["code"] == BEPR.E_BEPR_NOT_FOUND
          and missing["dir"] == ""
          and rc_missing == 2
          and BEPR.E_BEPR_NOT_FOUND in out_missing
          and ambiguous["code"] == BEPR.E_BEPR_AMBIGUOUS
          and rc_twice == 2
          and BEPR.E_BEPR_AMBIGUOUS in out_twice
          and "lab" in out_twice)
    if not ok:
        print("  measured: missing=%r rc=%r twice=%r rc2=%r"
              % (missing["code"], rc_missing, ambiguous["code"], rc_twice))
    drop_world(nowhere)
    drop_world(twice)
    check(ok, "AC-BEPR4 a bare filename that lives nowhere refuses with its "
              "own code at exit 2 instead of reading a pile it cannot prove")


def ac_bepr5():
    """CLI codes 0/2/3/5 and a byte-stable --json over the pinned GUARD_KEYS."""
    world = make_world(clean_piles=("qa",))
    foreign_bare = "reconcile-all-R9002.log"
    write(os.path.join(world, "elsewhere", foreign_bare),
          log_text((FOREIGN_NAME,)))
    # A pile that exists but carries no evidence the reader recognises is the
    # honest "unreadable" leg: the bare name resolves there, and the pile
    # cannot be read at all.
    write(os.path.join(world, "void", "notes.log"), "no evidence here\n")
    unreadable_bare = "notes.log"
    rc_clean, _, _ = run_cli(["--check", BARE, "--root", world])
    rc_foreign, _, _ = run_cli(["--check", foreign_bare, "--root", world])
    rc_missing, _, _ = run_cli(["--check", "absent-R9005.log", "--root", world])
    rc_unreadable, _, _ = run_cli(["--check", unreadable_bare, "--root", world])
    rc_bad, _, _ = run_cli(["--nope"])
    rc_j1, json_one, _ = run_cli(["--check", BARE, "--root", world, "--json"])
    rc_j2, json_two, _ = run_cli(["--check", BARE, "--root", world, "--json"])
    try:
        payload = json.loads(json_one)
        keys = list(payload.keys())
    except ValueError:
        keys = []
    ok = (rc_clean == 0 and rc_foreign == 2 and rc_missing == 2
          and rc_unreadable == 3 and rc_bad == 5
          and rc_j1 == 0 and rc_j2 == 0
          and json_one == json_two and tuple(keys) == FSFW.GUARD_KEYS)
    if not ok:
        print("  measured: rc=%r/%r/%r/%r/%r json_equal=%r keys=%r"
              % (rc_clean, rc_foreign, rc_missing, rc_unreadable, rc_bad,
                 json_one == json_two, keys))
    drop_world(world)
    check(ok, "AC-BEPR5 CLI codes 0/2/3/5 and a byte-stable --json over the "
              "pinned GUARD_KEYS are unchanged")


def ac_bepr6():
    """Pure ASCII stdlib, no clock/network/default pile, wired into the wire."""
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
    no_default_pile = 'DEFAULT_DIR =' not in text
    with open(WIRE, "rb") as handle:
        wire_text = handle.read().decode("ascii", "replace")
    start = wire_text.find("def matrix_section")
    end = wire_text.find("def render")
    section = wire_text[start:end] if start >= 0 and end > start else ""
    wire_asks = ("bare_evidence_pile_refusal as BEPR" in section
                 and "BEPR.is_bare(evidence)" in section
                 and "BEPR.pile_for(evidence, root)" in section)
    fges_kept = "FGES.evidence_dir(evidence)" in section
    wire_os_free = "import os" not in wire_text
    with open(RUNNER, "rb") as handle:
        runner_text = handle.read().decode("ascii", "replace")
    wired = LABEL in runner_text
    ok = (ascii_ok and pure and no_default_pile and wire_asks
          and fges_kept and wire_os_free and wired)
    if not ok:
        print("  measured: ascii=%r pure=%r no_default=%r asks=%r fges=%r "
              "osfree=%r wired=%r"
              % (ascii_ok, pure, no_default_pile, wire_asks, fges_kept,
                 wire_os_free, wired))
    check(ok, "AC-BEPR6 pure ASCII, stdlib only, zero network, no clock, no "
              "default pile, asked by the matrix section at call time, plus "
              "its own reconcile label")


def main():
    print("bare_evidence_pile_refusal suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_bepr1()
    ac_bepr2()
    ac_bepr3()
    ac_bepr4()
    ac_bepr5()
    ac_bepr6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())