"""followup_section_foreign_wire suite (R2370; criteria AC-FSFW1..AC-FSFW6 were
pre-registered inside the R2357 seed row of state/queue/tech.md BEFORE this
code existed).

What this proves: the follow-up matrix section now ASKS the foreign-section
reader first, so a ritual rename refuses the section instead of regenerating
the matrix over foreign sections in silence - and a clean pile behaves exactly
as it did before the wire.

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
import followup_section_foreign as FSF  # noqa: E402
import followup_section_foreign_wire as FSFW  # noqa: E402
import matrix_stamp_compare as MSC  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "followup_section_foreign_wire.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-followup-section-foreign-wire"
REPO_DOC = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")


def stamp_line():
    """R2418: the matrix section now refuses a doc with no stamp line, so the
    stand-in doc carries the SHIPPED doc's own stamp line, taken through the
    law rather than spelled here."""
    verdict, _code, stamp, _detail = MSC.stamp_of(REPO_DOC)
    if verdict != MSC.PASS or not stamp:
        return None
    with io.open(REPO_DOC, "r", encoding="utf-8") as handle:
        for line in handle.read().split("\n"):
            if stamp in line:
                return line
    return None


STAMP_LINE = stamp_line()
DOC_BYTES = (("%s\nMATRIX\n" % STAMP_LINE) if STAMP_LINE
             else "MATRIX\n").encode("utf-8")
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


def make_world(names=("matrix", "fingerprint", "profile", "census"),
               round_label="R9001", tool=True, doc=True, qa=True):
    """A stand-in root: one evidence log, the matrix doc, optionally the tool."""
    world = tempfile.mkdtemp(prefix="bigdomain-fsfw-w-")
    if tool:
        write(os.path.join(world, "src", "sandbox", "suite_matrix.py"),
              "print('stub')\n")
    if doc:
        path = os.path.join(world, "docs", "sandbox-suite-matrix.md")
        if not os.path.isdir(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        with open(path, "wb") as handle:
            handle.write(DOC_BYTES)
    if qa:
        write(os.path.join(world, "qa", "reconcile-all-%s.log" % round_label),
              log_text(names, round_label))
    return world


def drop_world(world):
    shutil.rmtree(world, ignore_errors=True)


def doc_bytes(world):
    path = os.path.join(world, "docs", "sandbox-suite-matrix.md")
    if not os.path.isfile(path):
        return None
    with open(path, "rb") as handle:
        return handle.read()


def fake_call(world, calls, body=DOC_BYTES):
    """A stand-in for the four tools: writes the temp matrix, counts the call."""
    def call(cmd):
        calls.append(list(cmd))
        if "--out" in cmd:
            target = cmd[cmd.index("--out") + 1]
            with open(target, "wb") as handle:
                handle.write(body)
            return 0, "PASS generated matrix\n"
        return 0, "PASS check: byte-identical (%d bytes, 1 suites)\n" % len(body)
    return call


def digest_files(paths):
    out = []
    for path in paths:
        with open(path, "rb") as handle:
            out.append((path, handle.read()))
    return tuple(out)


def run_cli(args):
    proc = subprocess.run([sys.executable, MODULE] + args,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          cwd=REPO)
    return (proc.returncode,
            proc.stdout.decode("ascii", "replace"),
            proc.stderr.decode("ascii", "replace"))


def ac_fsfw1():
    """The reading is imported; a patched reading flows through; no second parse."""
    world = make_world()
    real = FSF.reading
    doctored = {"dir": "qa", "vocabulary": list(VOCAB),
                "rounds": [{"round": "R9001", "evidence": "qa/x.log",
                            "reading": FSF.READING_FOREIGN,
                            "foreign": ["RENAMED"]}],
                "counts": {"rounds": 1, "clean": 0, "foreign": 1},
                "census": {"vocabulary": list(VOCAB), "foreign": ["RENAMED"],
                           "missing": []},
                "verdict": FSF.VERDICT_FOREIGN}
    clean = {"dir": "qa", "vocabulary": list(VOCAB),
             "rounds": [{"round": "R9001", "evidence": "qa/x.log",
                         "reading": FSF.READING_CLEAN, "foreign": []}],
             "counts": {"rounds": 1, "clean": 1, "foreign": 0},
             "census": {"vocabulary": list(VOCAB), "foreign": [],
                        "missing": []},
             "verdict": FSF.VERDICT_CLEAN}
    try:
        FSF.reading = lambda root, directory="qa": doctored
        moved = FSFW.guard(world)
        FSF.reading = lambda root, directory="qa": clean
        stays = FSFW.guard(world)
    finally:
        FSF.reading = real
        drop_world(world)
    with open(MODULE, "rb") as handle:
        raw = handle.read()
    text = raw.decode("ascii", "replace")
    second_parse = any(token in text for token in
                       ("os.listdir", "NAME_RE", "def parse", "read_log"))
    ok = (moved["verdict"] == FSF.VERDICT_FOREIGN
          and moved["rounds_foreign"] == ["R9001"]
          and moved["foreign"] == ["RENAMED"]
          and stays["verdict"] == FSF.VERDICT_CLEAN
          and stays["rounds_foreign"] == []
          and not second_parse)
    if not ok:
        print("  measured: moved=%r stays=%r second_parse=%r"
              % (moved, stays, second_parse), flush=True)
    check(ok, "AC-FSFW1 reading imported from the reader, patched reading flows")


def ac_fsfw2():
    """A FOREIGN-SECTION pile refuses naming round and names, no matrix byte."""
    world = make_world(names=("matrix", FOREIGN_NAME), tool=False)
    calls = []
    try:
        before = doc_bytes(world)
        entry, body = FSFW.matrix_section(world, "qa/reconcile-all-R9001.log",
                                          fake_call(world, calls))
        after = doc_bytes(world)
        reading = FSFW.guard(world)
    finally:
        drop_world(world)
    ok = (reading["verdict"] == FSF.VERDICT_FOREIGN
          and entry["verdict"] == "FAIL"
          and entry["detail"].startswith(FSFW.E_FSFW_FOREIGN_SECTION)
          and "R9001" in entry["detail"] and FOREIGN_NAME in entry["detail"]
          and body == "" and calls == [] and before == after == DOC_BYTES
          and "E_BFU_NO_TOOL" not in entry["detail"])
    if not ok:
        print("  measured: reading=%r entry=%r calls=%d doc=%r"
              % (reading, entry, len(calls), before), flush=True)
    check(ok, "AC-FSFW2 foreign pile refuses before any matrix byte")


def ac_fsfw3():
    """A clean pile reproduces the pre-wire matrix section byte for byte."""
    plain = make_world()
    wired = make_world()
    core_calls = []
    wire_calls = []
    try:
        core_entry, core_body = BF.matrix_core(
            plain, "qa/reconcile-all-R9001.log", fake_call(plain, core_calls))
        wire_entry, wire_body = FSFW.matrix_section(
            wired, "qa/reconcile-all-R9001.log", fake_call(wired, wire_calls))
        plain_doc = doc_bytes(plain)
        wired_doc = doc_bytes(wired)
        reading = FSFW.guard(wired)
    finally:
        drop_world(plain)
        drop_world(wired)
    ok = (reading["verdict"] == FSF.VERDICT_CLEAN
          and wire_entry == core_entry
          and wire_body == core_body
          and plain_doc == wired_doc == DOC_BYTES
          and len(core_calls) == len(wire_calls) == 2)
    if not ok:
        print("  measured: core=%r wire=%r docs=%r/%r"
              % (core_entry, wire_entry, plain_doc, wired_doc), flush=True)
    check(ok, "AC-FSFW3 clean pile matrix section byte-identical to pre-wire")


def ac_fsfw4():
    """A census disagreement is reported even when every round reads clean."""
    world = make_world(names=("matrix",))
    calls = []
    try:
        reading = FSFW.guard(world)
        entry, _body = FSFW.matrix_section(
            world, "qa/reconcile-all-R9001.log", fake_call(world, calls))
        census = reading["census"]
        union_law = set(census["foreign"]) == set()
    finally:
        drop_world(world)
    ok = (reading["verdict"] == FSF.VERDICT_CLEAN
          and reading["rounds_foreign"] == []
          and census["missing"] == ["census", "fingerprint", "profile"]
          and census["foreign"] == []
          and union_law
          and entry["verdict"] == "PASS"
          and "census missing=census,fingerprint,profile"
          in entry["detail"])
    if not ok:
        print("  measured: reading=%r entry=%r"
              % (reading["census"], entry), flush=True)
    check(ok, "AC-FSFW4 census disagreement reported on a clean pile")


def ac_fsfw5():
    """CLI 0 / 2 / 3 / 5, --json pinned and byte-stable, doc never written."""
    clean = make_world()
    foreign = make_world(names=("matrix", FOREIGN_NAME))
    bare = make_world(qa=False)
    try:
        green = run_cli(["--root", clean, "--check", "--json"])
        again = run_cli(["--root", clean, "--check", "--json"])
        red = run_cli(["--root", foreign, "--check"])
        unreadable = run_cli(["--root", bare, "--check"])
        no_flag = run_cli(["--root", clean])
        bad_flag = run_cli(["--root", clean, "--check", "--nonsense"])
        before = digest_files([os.path.join(foreign, "docs",
                                            "sandbox-suite-matrix.md")])
        run_cli(["--root", foreign, "--check"])
        after = digest_files([os.path.join(foreign, "docs",
                                          "sandbox-suite-matrix.md")])
    finally:
        drop_world(clean)
        drop_world(foreign)
        drop_world(bare)
    keys = list(json.loads(green[1]).keys()) if green[1].strip() else []
    ok = (green[0] == 0 and '"verdict": "VOCABULARY-CLEAN"' in green[1]
          and green == again
          and red[0] == 2 and "verdict=FOREIGN-SECTION" in red[1]
          and FOREIGN_NAME in red[1]
          and unreadable[0] == 3 and "UNREADABLE" in unreadable[1]
          and no_flag[0] == 5 and bad_flag[0] == 5
          and keys == list(FSFW.GUARD_KEYS)
          and before == after)
    if not ok:
        print("  measured: green=%r red=%r unreadable=%r keys=%r"
              % (green[0], red[0], unreadable[0], keys), flush=True)
    check(ok, "AC-FSFW5 CLI 0/2/3/5, --json pinned, doc untouched")


def ac_fsfw6():
    """Purity, clockless, and its own reconcile label."""
    with open(MODULE, "rb") as handle:
        raw = handle.read()
    try:
        raw.decode("ascii")
        ascii_only = True
    except UnicodeDecodeError:
        ascii_only = False
    text = raw.decode("ascii", "replace")
    blocked = ("import socket", "import urllib", "import http",
               "import requests", "urlopen", "time.time", "datetime",
               "import os", "open(")
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        wiring = handle.read()
    wired = (LABEL in wiring) and ("test_followup_section_foreign_wire.py"
                                   in wiring)
    ok = (ascii_only and not any(token in text for token in blocked)
          and "import followup_section_foreign as FSF" in text
          and wired)
    if not ok:
        print("  measured: ascii=%r wired=%r blocked=%r"
              % (ascii_only, wired,
                 [token for token in blocked if token in text]), flush=True)
    check(ok, "AC-FSFW6 ASCII, stdlib, clockless, wired in the registry")


def main():
    print("followup_section_foreign_wire suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_fsfw1()
    ac_fsfw2()
    ac_fsfw3()
    ac_fsfw4()
    ac_fsfw5()
    ac_fsfw6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())