# test_library_declaration_dialect_sweep.py - six criteria for the sweep that
# names every LIBRARY writer of a JSON declaration, and for the four writers
# that now ask the one shared dialect law at CALL time.
# Criteria AC-LDWS1..AC-LDWS6 were pre-registered inside the R2406 seed row of
# state/queue/tech.md BEFORE any code existed.
#
# Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.

import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import declaration_writer_dialect_preservation as DWD  # noqa: E402
import gate_decl_append as GDA  # noqa: E402
import gate_decl_retire as GDRT  # noqa: E402
import library_declaration_dialect_sweep as LDS  # noqa: E402
import machine_gate as MG  # noqa: E402
import orphan_promotion_ledger as OPL  # noqa: E402
import repin_dialect_preservation as RDP  # noqa: E402
import retire_accept as RA  # noqa: E402

EXPECTED_CRITERIA = 6
PASSES = []
FAILS = []

WRITERS = ("gate_decl_append.py", "gate_decl_retire.py",
           "orphan_promotion_ledger.py", "retire_accept.py")

# the four wired writers, as modules, with the post text each would land
WIRED = (
    ("gate_decl_append", GDA, "{\n  \"gates\": []\n}\n"),
    ("gate_decl_retire", GDRT, "{\n  \"gates\": []\n}\n"),
    ("orphan_promotion_ledger", OPL, "{\n  \"entries\": []\n}\n"),
    ("retire_accept", RA, "{\n  \"accepted\": []\n}\n"),
)


def check(ok, name):
    if ok:
        PASSES.append(name)
        print("  PASS %s" % name, flush=True)
    else:
        FAILS.append(name)
        print("  FAIL %s" % name, flush=True)


def read_text(path):
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def read_bytes(path):
    with io.open(path, "rb") as handle:
        return handle.read()


def source_of(name):
    return read_text(os.path.join(HERE, name))


def code_set(text):
    return sorted(set(re.findall(r"E_[A-Z0-9]+", text)))


def make_world(base, files):
    """A stand-in tree with <base>/src/os/<name> = <text>."""
    osdir = os.path.join(base, "src", "os")
    os.makedirs(osdir)
    for name, text in files:
        with io.open(os.path.join(osdir, name), "w", encoding="utf-8",
                     newline="\n") as handle:
            handle.write(text)
    return base


DECL_STUB = (
    "import io\n"
    "import json\n"
    "import os\n"
    "DECL_REL = \"state/thing.json\"\n"
    "TEMP_SUFFIX = \".tmp\"\n"
    "def land(path, payload):\n"
    "    text = json.dumps(payload, indent=2)\n"
    "    temp = path + TEMP_SUFFIX\n"
    "    with io.open(temp, \"wb\") as handle:\n"
    "        handle.write(text.encode(\"utf-8\"))\n"
    "    os.replace(temp, path)\n"
)

GENERAL_STUB = (
    "import io\n"
    "import json\n"
    "import os\n"
    "TEMP_SUFFIX = \".tmp\"\n"
    "def land(path, payload):\n"
    "    text = json.dumps(payload, indent=2)\n"
    "    temp = path + TEMP_SUFFIX\n"
    "    with io.open(temp, \"wb\") as handle:\n"
    "        handle.write(text.encode(\"utf-8\"))\n"
    "    os.replace(temp, path)\n"
)


def ac_ldws1():
    """The reading is derived from the source, and history is separated."""
    base = tempfile.mkdtemp(prefix="ldws1-")
    try:
        make_world(base, [
            ("decl_writer.py", DECL_STUB),
            ("closeout_R9999.py", DECL_STUB),
            ("plain_writer.py", GENERAL_STUB),
            ("test_decl_writer.py", DECL_STUB),
        ])
        reading = LDS.report(base)
        names = dict((row["name"], row["kind"]) for row in reading["rows"])
        derived = (names.get("decl_writer.py") == "DECLARATION"
                   and names.get("closeout_R9999.py") == "HISTORICAL"
                   and names.get("plain_writer.py") == "GENERAL"
                   and "test_decl_writer.py" not in names
                   and reading["library"] == 1
                   and reading["historical"] == 1
                   and reading["general"] == 1
                   and reading["unrouted"] == 1
                   and reading["verdict"] == "SWEEP-DEBT")
        module_text = source_of("library_declaration_dialect_sweep.py")
        no_whitelist = not any(writer[:-3] in module_text for writer in WRITERS)
        ok = derived and no_whitelist
        if not ok:
            print("  measured: kinds=%r reading=%r whitelist=%r"
                  % (names, reading, no_whitelist), flush=True)
        check(ok, "AC-LDWS1 source-derived sweep separates history, no whitelist")
    finally:
        shutil.rmtree(base, ignore_errors=True)


def ac_ldws2():
    """Each declaration writer asks the shared derivation at CALL time."""
    stamped = b"PATCHED"
    original = DWD.encode

    def fake(raw, composed):
        return "LF", stamped

    moved = True
    try:
        DWD.encode = fake
        for label, module, post in WIRED:
            if module.payload_bytes(b"", post) != stamped:
                moved = False
                print("  measured: %s did not move" % label, flush=True)
    finally:
        DWD.encode = original
    reading = LDS.report(ROOT)
    routed = sorted(name for name in reading["rows"]
                    if row_kind(reading, name) == "DECLARATION")
    all_routed = (reading["verdict"] == "SWEEP-CLEAN"
                  and reading["routed"] == reading["library"]
                  and reading["library"] >= len(WRITERS))
    repin_asks = "repin_dialect_preservation" in source_of(
        "residue_triage_repin.py")
    ok = moved and all_routed and repin_asks and RDP is not None
    if not ok:
        print("  measured: moved=%r routed=%r library=%r repin=%r"
              % (moved, reading["routed"], reading["library"], repin_asks),
              flush=True)
    check(ok, "AC-LDWS2 every declaration writer asks the law at call time")


def row_kind(reading, name):
    for row in reading["rows"]:
        if row["name"] == name:
            return row["kind"]
    return None


def ac_ldws3():
    """An LF declaration keeps exactly today's bytes on all four writers."""
    ok = True
    for label, module, post in WIRED:
        raw = post.encode("utf-8")
        got = module.payload_bytes(raw, post)
        if got != post.encode("utf-8"):
            ok = False
            print("  measured: %s moved on LF" % label, flush=True)
    reading = LDS.report(ROOT)
    real = all(row["kind"] != "DECLARATION" or row["routed"]
               for row in reading["rows"])
    ok = ok and real and reading["general"] > 0
    check(ok, "AC-LDWS3 an LF declaration keeps today's bytes")


def ac_ldws4():
    """A CRLF declaration keeps CRLF, and a real write proves it."""
    ok = True
    for label, module, post in WIRED:
        raw = post.replace("\n", "\r\n").encode("utf-8")
        got = module.payload_bytes(raw, post)
        crlf = got.replace(b"\r\n", b"")
        if b"\n" in crlf or b"\r" in crlf or b"\r\n" not in got:
            ok = False
            print("  measured: %s did not keep CRLF" % label, flush=True)
    base = tempfile.mkdtemp(prefix="ldws4-")
    try:
        decl = os.path.join(base, MG.DEFAULT_DECLARATION)
        os.makedirs(os.path.dirname(decl))
        body = {"version": 1, "declared_by": "R2409",
                "reason": "crlf proof world", "gates": []}
        with io.open(decl, "wb") as handle:
            handle.write((json.dumps(body, indent=2) + "\n")
                         .replace("\n", "\r\n").encode("utf-8"))
        report = GDA.append_gate(base, "-#ACLDWS4", "battery",
                                 "crlf proof", "R2409", execute=True)
        landed = read_bytes(decl)
        lone = landed.replace(b"\r\n", b"")
        stays = (b"\r\n" in landed and b"\n" not in lone and b"\r" not in lone
                 and report["read_back_ok"] is True)
        ok = ok and stays
        if not stays:
            print("  measured: landed crlf=%r report=%r"
                  % (b"\r\n" in landed, report), flush=True)
    finally:
        shutil.rmtree(base, ignore_errors=True)
    check(ok, "AC-LDWS4 a CRLF declaration stays CRLF after the real write")


def ac_ldws5():
    """Every pre-existing refusal code and exit path is unchanged."""
    ok = True
    for name in WRITERS:
        head = subprocess.run(
            ["git", "show", "HEAD:src/os/" + name],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if head.returncode != 0:
            ok = False
            print("  measured: git show failed for %s" % name, flush=True)
            continue
        before = code_set(head.stdout.decode("utf-8", "replace"))
        after = code_set(source_of(name))
        if before != after:
            ok = False
            print("  measured: %s codes moved %r -> %r"
                  % (name, before, after), flush=True)
    base = tempfile.mkdtemp(prefix="ldws5-")
    try:
        decl = os.path.join(base, MG.DEFAULT_DECLARATION)
        os.makedirs(os.path.dirname(decl))
        with io.open(decl, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(
                {"version": 1, "declared_by": "R2409", "reason": "dup world",
                 "gates": [
                    {"identity": "-#ACLDWS5", "capability": "battery",
                     "reason": "dup", "declared_by": "R2409"}]}, indent=2))
            handle.write("\n")
        run = subprocess.run(
            [sys.executable, os.path.join(HERE, "gate_decl_append.py"),
             "--root", base, "--identity", "-#ACLDWS5", "--capability",
             "battery", "--reason", "dup", "--declared-by", "R2409"],
            cwd=base, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        text = run.stdout.decode("utf-8", "replace")
        untouched = read_bytes(decl)
        ok = ok and run.returncode == 2 and "E_GDA_DUP" in text
        if not (run.returncode == 2 and "E_GDA_DUP" in text):
            print("  measured: rc=%r out=%r" % (run.returncode, text[:120]),
                  flush=True)
        if b"ACLDWS5" not in untouched:
            ok = False
    finally:
        shutil.rmtree(base, ignore_errors=True)
    check(ok, "AC-LDWS5 pre-existing refusals unchanged, proved on HEAD")


def ac_ldws6():
    """Pure, stdlib only, no clock, no network, wired with its own label."""
    text = source_of("library_declaration_dialect_sweep.py")
    ascii_only = all(ord(char) < 128 for char in text)
    no_net = not re.search(r"\b(urllib|socket|http|requests)\b", text)
    no_clock = not re.search(r"\b(time|datetime)\.", text)
    stdlib_only = set(["os", "re", "ast", "json", "sys", "warnings"]) >= set(
        name for name in re.findall(r"^import ([a-z_]+)$", text, re.M))
    runner = read_text(os.path.join(ROOT, "src", "sandbox", "reconcile_all.py"))
    wired = ("\"os-library-declaration-dialect-sweep\","
             in runner.replace("\n", "")) or (
        "os-library-declaration-dialect-sweep" in runner)
    own_label = LDS.SUITE_LABEL == "os-library-declaration-dialect-sweep"
    writes = "os.replace" in text and "open(.*\"wb\"" in text
    ok = (ascii_only and no_net and no_clock and stdlib_only and wired
          and own_label and not writes)
    if not ok:
        print("  measured: ascii=%r net=%r clock=%r wired=%r label=%r"
              % (ascii_only, no_net, no_clock, wired, own_label), flush=True)
    check(ok, "AC-LDWS6 pure, stdlib only and wired with its own label")


def main():
    print("library_declaration_dialect_sweep suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_ldws1()
    ac_ldws2()
    ac_ldws3()
    ac_ldws4()
    ac_ldws5()
    ac_ldws6()
    verdict = "SUITE PASS" if not FAILS else "SUITE FAIL"
    print("%s %d/%d" % (verdict, len(PASSES), len(PASSES) + len(FAILS)),
          flush=True)
    if (len(PASSES) + len(FAILS)) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (len(PASSES) + len(FAILS), EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())