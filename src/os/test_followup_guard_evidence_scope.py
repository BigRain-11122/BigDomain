"""followup_guard_evidence_scope suite (R2380; criteria AC-FGES1..AC-FGES6 were

pre-registered inside the R2370 seed row of state/queue/tech.md BEFORE this
code existed).

What this proves: the follow-up matrix section guards the pile the EVIDENCE
belongs to rather than a hard-coded 'qa', so the refusal and the matrix always
describe the same logs - and an evidence path under qa keeps the old reading
byte for byte.

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

import battery_followup as BF  # noqa: E402
import followup_guard_evidence_scope as FGES  # noqa: E402
import followup_section_foreign as FSF  # noqa: E402
import followup_section_foreign_wire as FSFW  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "followup_section_foreign_wire.py")
HELPER = os.path.join(BASE, "followup_guard_evidence_scope.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-followup-guard-evidence-scope"
DOC_BYTES = b"MATRIX\n"
FOREIGN_NAME = "FOREIGN_RITUAL"
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


def log_text(names, round_label="R9001", verdict="PASS"):
    lines = ["SECTION %s PASS detail" % name for name in names]
    lines.append("VERDICT %s %s" % (round_label, verdict))
    return "\n".join(lines) + "\n"


def make_world(directory="qa", names=VOCAB, round_label="R9001"):
    """A stand-in root: one evidence pile, the matrix doc and the tool stub."""
    world = tempfile.mkdtemp(prefix="bigdomain-fges-w-")
    write(os.path.join(world, "src", "sandbox", "suite_matrix.py"),
          "print('stub')\n")
    path = os.path.join(world, "docs", "sandbox-suite-matrix.md")
    if not os.path.isdir(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    with open(path, "wb") as handle:
        handle.write(DOC_BYTES)
    write(os.path.join(world, directory,
                       "reconcile-all-%s.log" % round_label),
          log_text(names, round_label))
    return world


def drop_world(world):
    shutil.rmtree(world, ignore_errors=True)


def fake_call(body=DOC_BYTES):
    """A stand-in for the four tools: writes the temp matrix, counts the call."""
    def call(cmd):
        if "--out" in cmd:
            target = cmd[cmd.index("--out") + 1]
            with open(target, "wb") as handle:
                handle.write(body)
            return 0, "PASS generated matrix\n"
        return 0, "PASS check: byte-identical (%d bytes, 1 suites)\n" % len(body)
    return call


def run_cli(args):
    proc = subprocess.run([sys.executable, MODULE] + args,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          cwd=REPO)
    return (proc.returncode,
            proc.stdout.decode("ascii", "replace"),
            proc.stderr.decode("ascii", "replace"))


def ac_fges1():
    """The guarded directory is derived, and a patched derivation moves it."""
    world = make_world()
    write(os.path.join(world, "other", "reconcile-all-R9002.log"),
          log_text((FOREIGN_NAME,), "R9002"))
    real = FGES.evidence_dir
    try:
        FGES.evidence_dir = lambda evidence, default="qa": "other"
        moved, moved_body = FSFW.matrix_section(
            world, "qa/reconcile-all-R9001.log", fake_call())
    finally:
        FGES.evidence_dir = real
    stays, stays_body = FSFW.matrix_section(
        world, "qa/reconcile-all-R9001.log", fake_call())
    expected_entry, expected_body = BF.matrix_core(
        world, "qa/reconcile-all-R9001.log", fake_call())
    with open(MODULE, "rb") as handle:
        text = handle.read().decode("ascii", "replace")
    start = text.find("def matrix_section")
    end = text.find("def render")
    section_text = text[start:end] if start >= 0 and end > start else ""
    literal_default = 'directory="qa"' in section_text
    derived = "FGES.evidence_dir(evidence)" in section_text
    ok = (moved["verdict"] == "FAIL"
          and FSFW.E_FSFW_FOREIGN_SECTION in moved["detail"]
          and moved_body == ""
          and stays["verdict"] == "PASS"
          and stays["verdict"] == expected_entry["verdict"]
          and stays_body == expected_body
          and derived and not literal_default)
    if not ok:
        print("  measured: moved=%r stays=%r derived=%r literal=%r"
              % (moved, stays["verdict"], derived, literal_default))
    drop_world(world)
    check(ok, "AC-FGES1 the guarded directory is derived from the evidence "
              "path and a patched derivation moves which pile is read")


def ac_fges2():
    """An evidence path under qa keeps the old section report byte for byte."""
    world = make_world()
    entry, body = FSFW.matrix_section(
        world, "qa/reconcile-all-R9001.log", fake_call())
    expected_entry, expected_body = BF.matrix_core(
        world, "qa/reconcile-all-R9001.log", fake_call())
    derived = FGES.evidence_dir("qa/reconcile-all-R9001.log")
    ok = (entry == expected_entry and body == expected_body
          and derived == "qa")
    if not ok:
        print("  measured: derived=%r entry=%r expected=%r"
              % (derived, entry, expected_entry))
    drop_world(world)
    check(ok, "AC-FGES2 an evidence path under qa keeps the section report "
              "byte-identical to the R2370 wire")


def ac_fges3():
    """A pile the evidence lives in that reads FOREIGN-SECTION refuses."""
    world = make_world()
    write(os.path.join(world, "elsewhere", "reconcile-all-R9002.log"),
          log_text((FOREIGN_NAME,), "R9002"))
    entry, body = FSFW.matrix_section(
        world, "elsewhere/reconcile-all-R9002.log", fake_call())
    qa_reading = FSFW.guard(world, "qa")
    ok = (entry["verdict"] == "FAIL"
          and FSFW.E_FSFW_FOREIGN_SECTION in entry["detail"]
          and body == ""
          and qa_reading["verdict"] == FSF.VERDICT_CLEAN)
    if not ok:
        print("  measured: entry=%r qa=%r" % (entry, qa_reading["verdict"]))
    drop_world(world)
    check(ok, "AC-FGES3 an evidence pile that reads FOREIGN-SECTION refuses, "
              "proving the guard follows the MEASURED pile")


def ac_fges4():
    """A relative and an absolute path for the same file read one pile."""
    world = make_world()
    name = os.path.join("qa", "reconcile-all-R9001.log")
    rel = name.replace(os.sep, "/")
    absolute = os.path.join(world, name)
    rel_dir = FGES.evidence_dir(rel)
    abs_dir = FGES.evidence_dir(absolute)
    rel_entry, rel_body = FSFW.matrix_section(world, rel, fake_call())
    abs_entry, abs_body = FSFW.matrix_section(world, absolute, fake_call())
    ok = (rel_dir == abs_dir == "qa"
          and rel_entry == abs_entry and rel_body == abs_body)
    if not ok:
        print("  measured: rel=%r abs=%r entry=%r/%r"
              % (rel_dir, abs_dir, rel_entry, abs_entry))
    drop_world(world)
    check(ok, "AC-FGES4 a relative and an absolute evidence path read the same "
              "pile, so the refusal never depends on the working directory")


def ac_fges5():
    """CLI codes 0/2/3/5 and a byte-stable --json over the pinned keys."""
    world = make_world()
    write(os.path.join(world, "elsewhere", "reconcile-all-R9002.log"),
          log_text((FOREIGN_NAME,), "R9002"))
    rc_clean, out_clean, _ = run_cli(["--check", "qa", "--root", world])
    rc_foreign, out_foreign, _ = run_cli(
        ["--check", "elsewhere", "--root", world])
    rc_missing, _, _ = run_cli(["--check", "nowhere", "--root", world])
    rc_bad, _, _ = run_cli(["--nope"])
    rc_j1, json_one, _ = run_cli(["--check", "qa", "--root", world, "--json"])
    rc_j2, json_two, _ = run_cli(["--check", "qa", "--root", world, "--json"])
    try:
        payload = json.loads(json_one)
        keys = list(payload.keys())
    except ValueError:
        keys = []
    ok = (rc_clean == 0 and rc_foreign == 2 and rc_missing == 3
          and rc_bad == 5 and rc_j1 == 0 and rc_j2 == 0
          and json_one == json_two and tuple(keys) == FSFW.GUARD_KEYS)
    if not ok:
        print("  measured: rc=%r/%r/%r/%r json_equal=%r keys=%r"
              % (rc_clean, rc_foreign, rc_missing, rc_bad,
                 json_one == json_two, keys))
    drop_world(world)
    check(ok, "AC-FGES5 CLI codes 0/2/3/5 and a byte-stable --json over the "
              "pinned GUARD_KEYS are unchanged")


def ac_fges6():
    """Pure ASCII stdlib, no clock/network, reading still owned by FSF."""
    with open(HELPER, "rb") as handle:
        raw = handle.read()
    try:
        helper_text = raw.decode("ascii")
        ascii_ok = True
    except UnicodeDecodeError:
        helper_text = raw.decode("ascii", "replace")
        ascii_ok = False
    banned = ("socket", "urllib", "requests", "http.client", "time.time",
              "datetime", "import time")
    pure = not any(token in helper_text for token in banned)
    reading_owned = "import followup_section_foreign" not in helper_text
    with open(MODULE, "rb") as handle:
        wire_text = handle.read().decode("ascii", "replace")
    wire_still_imports = "import followup_section_foreign as FSF" in wire_text
    with open(RUNNER, "rb") as handle:
        runner_text = handle.read().decode("ascii", "replace")
    wired = LABEL in runner_text
    ok = (ascii_ok and pure and reading_owned and wire_still_imports and wired)
    if not ok:
        print("  measured: ascii=%r pure=%r reading_owned=%r wire=%r wired=%r"
              % (ascii_ok, pure, reading_owned, wire_still_imports, wired))
    check(ok, "AC-FGES6 pure ASCII, stdlib only, zero network, no clock, the "
              "reading still imported from followup_section_foreign, plus its "
              "own reconcile label")


def main():
    print("followup_guard_evidence_scope suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_fges1()
    ac_fges2()
    ac_fges3()
    ac_fges4()
    ac_fges5()
    ac_fges6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())