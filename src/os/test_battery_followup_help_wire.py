"""battery_followup_help_wire suite (R2366; criteria AC-BFH1..AC-BFH6 were
pre-registered inside the R2365 tech seed row of state/queue/tech.md line 412
BEFORE this code existed).

What this proves: the follow-up CLI now answers a bare `--help` as a QUESTION
at exit 0, and it answers it from two imported contracts rather than from a
retyped flag list - while every other exit code and every other printed line
stays byte-identical to what R2272 pinned.

The stub world below is the R2272 world: four stand-in tools, the matrix doc
and an evidence file, so a real section run costs nothing and touches nothing.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
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
import battery_followup_help_wire as HW  # noqa: E402
import runner_arg_guard as RAG  # noqa: E402
import matrix_stamp_compare as MSC  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "battery_followup.py")
WIRE = os.path.join(BASE, "battery_followup_help_wire.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-battery-followup-help-wire"
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


def stub(body):
    return "import sys\n" + body + "\n"


MATRIX_OK = stub(
    "a = sys.argv\n"
    "if '--out' in a:\n"
    "    open(a[a.index('--out') + 1], 'wb').write(%r)\n"
    "    print('PASS generated matrix')\n"
    "else:\n"
    "    print('PASS check: byte-identical (7 bytes, 1 suites)')\n" % DOC_BYTES)

CENSUS_OK = stub("print('CENSUS DRIFT-CLEAN files=0 flags=0')")
FP_OK = stub("print('FINGERPRINT chain CLEAN domains=5')")
PROF_OK = stub("print('PROFILE daily check PASS')")
PROF_RED = stub("print('PROFILE drift')\nsys.exit(2)")


def write(path, text):
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def make_world(profile=PROF_OK, evidence=True):
    """A complete stand-in root: four stub tools, the doc, an evidence file."""
    world = tempfile.mkdtemp(prefix="bigdomain-bfh-w-")
    write(os.path.join(world, "src", "sandbox", "suite_matrix.py"), MATRIX_OK)
    write(os.path.join(world, "src", "sandbox", "fingerprint_regen.py"), FP_OK)
    write(os.path.join(world, "src", "sandbox", "runner_profile.py"), profile)
    write(os.path.join(world, "src", "os", "qa_writer_census.py"), CENSUS_OK)
    path = os.path.join(world, "docs", "sandbox-suite-matrix.md")
    if not os.path.isdir(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    with open(path, "wb") as handle:
        handle.write(DOC_BYTES)
    if evidence:
        write(os.path.join(world, "qa", "evidence.log"), "RUNNER PASS\n")
    return world


def drop_world(world):
    shutil.rmtree(world, ignore_errors=True)


def digest(path):
    with open(path, "rb") as handle:
        return handle.read()


def run_cli(module, args, cwd=None):
    proc = subprocess.run([sys.executable, module] + args,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          cwd=cwd or REPO)
    return (proc.returncode,
            proc.stdout.decode("ascii", "replace"),
            proc.stderr.decode("ascii", "replace"))


def ac_bfh1():
    """Both halves are imported: patching either moves the printed answer."""
    world = make_world()
    try:
        base = HW.usage_text()
        real_takes = BF.TAKES
        real_flags = BF.FLAGS
        real_load = RAG.load_contract
        real_runner = HW.load_runner_contract

        BF.TAKES = dict(real_takes)
        BF.TAKES["--audit"] = "audit"
        moved_takes = HW.usage_text()

        BF.FLAGS = dict(real_flags)
        BF.FLAGS["--loud"] = "loud"
        moved_flags = HW.usage_text()

        BF.TAKES = real_takes
        BF.FLAGS = real_flags

        patched = dict(real_load())
        patched["name"] = "patched-runner.py"
        patched["known_flags"] = ("--made-up",)
        RAG.load_contract = lambda path=None: dict(patched)
        moved_house = HW.usage_text()

        RAG.load_contract = lambda path=None: {"name": "x"}
        refused = None
        try:
            HW.usage_text()
        except HW.HelpWireError as exc:
            refused = exc.code

        RAG.load_contract = real_load
        live = HW.usage_text()

        with io.open(WIRE, "r", encoding="ascii") as handle:
            source = handle.read()
        no_table = ("--evidence" not in source and "--dry-run" not in source
                    and "--root" not in source)
    finally:
        HW.load_runner_contract = real_runner
        RAG.load_contract = real_load
        BF.TAKES = real_takes
        BF.FLAGS = real_flags
        drop_world(world)
    ok = ("--audit" in moved_takes and "--audit" not in base
          and "--loud" in moved_flags and "--loud" not in base
          and "patched-runner.py" in moved_house
          and "--made-up" in moved_house
          and refused == HW.E_BFH_NO_CONTRACT
          and "reconcile_all.py" in live
          and no_table)
    if not ok:
        print("  measured: takes=%r flags=%r house=%r refused=%r no_table=%r"
              % ("--audit" in moved_takes, "--loud" in moved_flags,
                 "patched-runner.py" in moved_house, refused, no_table),
              flush=True)
    check(ok, "AC-BFH1 both contracts imported; no second flag table")


def ac_bfh2():
    """A bare --help answers at exit 0 and runs no section."""
    world = make_world()
    evidence = os.path.join(world, "qa", "evidence.log")
    try:
        before = digest(evidence)
        code, out, err = run_cli(MODULE, ["--help"])
        short = run_cli(MODULE, ["-h"]) if False else None
        after = digest(evidence)
        # -h must answer the same question, but only through the parser.
        short = run_cli(MODULE, ["--evidence", "qa/evidence.log", "-h"],
                        cwd=world)
    finally:
        drop_world(world)
    ok = (code == 0 and "-h" in out and "--help" in out
          and "usage: battery_followup.py" in out
          and "SECTION " not in out and "VERDICT " not in out
          and "APPENDED" not in out and err == ""
          and before == after
          and short[0] == 0 and "usage: battery_followup.py" in short[1])
    if not ok:
        print("  measured: code=%r unchanged=%r out=%r short=%r"
              % (code, before == after, out[:120], short[0]), flush=True)
    check(ok, "AC-BFH2 bare --help answers at exit 0, no section runs")


def ac_bfh3():
    """An unknown flag is still refused at 2, naming the token."""
    world = make_world()
    try:
        wire_code, wire_out, _err = run_cli(WIRE, ["--nonsense"])
        live_code, live_out, _err = run_cli(WIRE, ["--help"])
    finally:
        drop_world(world)
    report = HW.classify(["--nonsense"])
    ok = (wire_code == 2 and "--nonsense" in wire_out
          and "ANSWER UNKNOWN_FLAG exit=2 flag=--nonsense" in wire_out
          and report["status"] == HW.STATUS_UNKNOWN
          and report["flag"] == "--nonsense"
          and report["exit"] == 2
          and live_code == 0 and "usage: battery_followup.py" in live_out
          and HW.classify(["--help"])["status"] == HW.STATUS_HELP
          and HW.classify([])["exit"] == 5)
    if not ok:
        print("  measured: wire=%r out=%r report=%r live=%r"
              % (wire_code, wire_out[:160], report, live_code), flush=True)
    check(ok, "AC-BFH3 unknown flag refused at 2 naming the token")


def ac_bfh4():
    """Every other exit code AND its printed line stays byte-identical."""
    world = make_world()
    red = make_world(profile=PROF_RED)
    gone = make_world(evidence=False)
    try:
        green = run_cli(MODULE, ["--root", world, "--evidence",
                                 "qa/evidence.log", "--label", "R2272",
                                 "--dry-run"])
        red_run = run_cli(MODULE, ["--root", red, "--evidence",
                                   "qa/evidence.log", "--dry-run"])
        missing = run_cli(MODULE, ["--root", gone, "--evidence",
                                   "qa/evidence.log", "--dry-run"])
        no_flag = run_cli(MODULE, ["--root", world, "--dry-run"])
        bad_flag = run_cli(MODULE, ["--root", world, "--evidence",
                                    "qa/evidence.log", "--nonsense"])
        bad_round = run_cli(MODULE, ["--root", world, "--evidence",
                                     "qa/evidence.log", "--round", "abc"])
        report, _bodies = BF.sections(world, "qa/evidence.log", "R2272")
    finally:
        drop_world(world)
        drop_world(red)
        drop_world(gone)
    pinned_green = BF.render(report)
    # The console translates "\n" to "\r\n" on this platform for EVERY CLI in
    # the tree; the criterion is about the printed LINE, so the transport EOL
    # is normalised before comparing and nothing else is.
    def line(text):
        return text.replace("\r\n", "\n")
    ok = (green[0] == 0 and line(green[1]) == pinned_green
          and red_run[0] == 2 and "failing=profile" in red_run[1]
          and missing[0] == 3
          and line(missing[1]) == "MISSING EVIDENCE qa/evidence.log\n"
          and no_flag[0] == 5
          and line(no_flag[1]) == "E_BFU_BAD_ARGS --evidence is required\n"
          and bad_flag[0] == 5
          and line(bad_flag[1]) == "E_BFU_BAD_ARGS --nonsense\n"
          and bad_round[0] == 5
          and line(bad_round[1])
          == "E_BFU_BAD_ARGS --round must be an integer\n")
    if not ok:
        print("  measured: %r %r %r %r %r %r %r"
              % (green[0], green[1] == pinned_green, red_run[0], missing[0],
                 no_flag[0], bad_flag[0], bad_round[0]), flush=True)
    check(ok, "AC-BFH4 other codes and printed lines byte-identical")


def ac_bfh5():
    """The --json faces stay byte-stable over their pinned keys."""
    world = make_world()
    try:
        one = run_cli(MODULE, ["--root", world, "--evidence",
                               "qa/evidence.log", "--label", "R2272",
                               "--dry-run", "--json"])
        two = run_cli(MODULE, ["--root", world, "--evidence",
                               "qa/evidence.log", "--label", "R2272",
                               "--dry-run", "--json"])
        wire_one = run_cli(WIRE, ["--help", "--json"])
        wire_two = run_cli(WIRE, ["--help", "--json"])
    finally:
        drop_world(world)
    payload = one[1].split("{", 1)
    keys = list(json.loads("{" + payload[1]).keys()) if len(payload) > 1 else []
    wire_payload = wire_one[1].split("{", 1)
    wire_keys = (list(json.loads("{" + wire_payload[1]).keys())
                 if len(wire_payload) > 1 else [])
    ok = (one == two and wire_one == wire_two
          and keys == list(BF.REPORT_KEYS)
          and wire_keys == list(HW.WIRE_KEYS))
    if not ok:
        print("  measured: stable=%r wire=%r keys=%r wire_keys=%r"
              % (one == two, wire_one == wire_two, keys, wire_keys),
              flush=True)
    check(ok, "AC-BFH5 --json byte-stable over pinned keys, both CLIs")


def ac_bfh6():
    """Purity, wiring, and the four sections still running after the change."""
    with open(WIRE, "rb") as handle:
        raw = handle.read()
    with open(MODULE, "rb") as handle:
        model = handle.read()
    ascii_ok = True
    for blob in (raw, model):
        try:
            blob.decode("ascii")
        except UnicodeDecodeError:
            ascii_ok = False
    text = raw.decode("ascii", "replace")
    blocked = ("import socket", "import urllib", "import http",
               "import requests", "urlopen", "time.time", "datetime")
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        wiring = handle.read()
    wired = ((LABEL in wiring)
             and ("test_battery_followup_help_wire.py" in wiring))
    world = make_world()
    try:
        report, bodies = BF.sections(world, "qa/evidence.log", "R2272")
    finally:
        drop_world(world)
    sections_ok = (report["verdict"] == "PASS" and len(bodies) == 4
                   and [e["section"] for e in report["sections"]]
                   == list(BF.SECTIONS))
    ok = (ascii_ok and not any(token in text for token in blocked)
          and "battery_followup_help_wire" in tool_source()
          and wired and sections_ok)
    if not ok:
        print("  measured: ascii=%r wired=%r sections=%r"
              % (ascii_ok, wired, sections_ok), flush=True)
    check(ok, "AC-BFH6 ASCII, no clock/network, wired, sections still run")


def tool_source():
    """Does the changed caller actually route its answer through this wire?"""
    with io.open(MODULE, "r", encoding="ascii") as handle:
        return handle.read()


def main():
    print("battery_followup_help_wire suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_bfh1()
    ac_bfh2()
    ac_bfh3()
    ac_bfh4()
    ac_bfh5()
    ac_bfh6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())