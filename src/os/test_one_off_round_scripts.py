"""one_off_round_scripts suite (R2838; criteria AC-OOS1..AC-OOS6 were pinned
in the R2838 row of src/os/backlog.md BEFORE this file existed - the pin row
was committed ahead of the code).

What this proves: two one-off families were retired (226 state_append_R*.py at
R2834, 682 export_R*/closeout_R*.py at R2837) and nothing refused the next one.
This suite pins the freeze-round law that does:

  - it is a reader: no write primitive, no clock, ASCII, stdlib, no network;
  - a one-off at or above the freeze round is refused and named;
  - a one-off below it, and every permanent module, is not refused;
  - the real tree reads OK and the numbers it prints are measurements;
  - an empty scope reads NONE, not CLEAN, and the exit codes are distinct.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
ROOT = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import one_off_round_scripts as OOS  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "one_off_round_scripts.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-one-off-round-scripts"

PASSES = 0
FAILS = 0

# File-write primitives only: sys.stdout.write is narration, not a write to
# disk, and the read-only proof is taken from the world's bytes below anyway.
WRITE_PRIMITIVES = ("write_text(", "write_bytes(", "mkstemp(", "os.replace(",
                    "shutil.", 'open(.*mode="w"')
NET_IMPORTS = ("urllib", "http.client", "requests", "socket", "httpx")
CLOCK_IMPORTS = ("import time", "import datetime", "time.time(")


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


def world(names):
    """A private tree whose src/os holds exactly these file names."""
    folder = tempfile.mkdtemp(prefix="oos-")
    scope = os.path.join(folder, "src", "os")
    os.makedirs(scope)
    for name in names:
        with io.open(os.path.join(scope, name), "w", encoding="utf-8",
                     newline="") as handle:
            handle.write("# fixture\n")
    return folder


def cleanup(folder):
    shutil.rmtree(folder, ignore_errors=True)


def fingerprint(folder):
    """sha256 + mtime of every file under the folder, for read-only proof."""
    rows = []
    for base, dirs, files in os.walk(folder):
        dirs.sort()
        for name in sorted(files):
            path = os.path.join(base, name)
            with io.open(path, "rb") as handle:
                digest = hashlib.sha256(handle.read()).hexdigest()
            rows.append((os.path.relpath(path, folder), digest,
                         os.stat(path).st_mtime_ns))
    return rows


def run_cli(argv):
    buf = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(buf):
        with contextlib.redirect_stderr(err):
            try:
                code = OOS.main(argv)
            except SystemExit as exc:
                code = exc.code
    return code, buf.getvalue(), err.getvalue()


def ac_oos1():
    """AC-OOS1: one read-only reader - no write, no clock, ASCII, stdlib."""
    source = io.open(MODULE, encoding="utf-8").read()
    try:
        source.encode("ascii")
        ascii_ok = True
    except UnicodeEncodeError:
        ascii_ok = False
    writes = [token for token in WRITE_PRIMITIVES if token in source]
    clocks = [token for token in CLOCK_IMPORTS if token in source]
    nets = [token for token in NET_IMPORTS if token in source]
    help_code, help_out, _ = run_cli(["--help"])
    # Read-only is proven on a real world, not asserted from the source alone.
    folder = world(["keep_me.py"])
    before = fingerprint(folder)
    run_cli(["--check", "--root", folder])
    run_cli(["--check", "--root", folder, "--scope", "src/os", "--json"])
    after = fingerprint(folder)
    try:
        ok = (ascii_ok and not writes and not clocks and not nets
              and help_code == 0 and "usage:" in help_out and before == after)
        if not ok:
            print("  measured: ascii=%r writes=%r clocks=%r net=%r help=%r "
                  "unchanged=%r" % (ascii_ok, writes, clocks, nets, help_code,
                                    before == after), flush=True)
    finally:
        cleanup(folder)
    check(ok, "AC-OOS1 the reader writes nothing, reads no clock, is ASCII, "
          "stdlib only, zero network, and --help exits 0")


def ac_oos2():
    """AC-OOS2: a one-off at or above the freeze is refused and named."""
    names = ["foo_R2838.py", "bar_R2999.py", "zap_R3000b.py", "old_R2431.py"]
    folder = world(names)
    try:
        code, out, _ = run_cli(["--check", "--root", folder])
        named = [n for n in names if n.endswith(".py") and ("REFUSE" in out
                 and n in out)]
        refused_named = set()
        for line in out.splitlines():
            if line.strip().startswith("REFUSE "):
                refused_named.add(os.path.basename(line.split()[1]))
        ok = (code == 2 and "verdict=REFUSE" in out
              and refused_named == {"foo_R2838.py", "bar_R2999.py",
                                    "zap_R3000b.py"})
        if not ok:
            print("  measured: code=%r refused=%r" % (code, sorted(refused_named)),
                  flush=True)
        del named
    finally:
        cleanup(folder)
    check(ok, "AC-OOS2 the three one-offs at or above the freeze are refused "
          "at round=2838/2999/3000 and read rc=2, old_R2431 is not refused")


def ac_oos3():
    """AC-OOS3: no false positives - sub-freeze one-offs and modules pass."""
    names = ["export_R2431.py", "fold_R2583b.py", "state_append.py",
             "export_round.py", "scan_five_still.py", "test_state_append.py"]
    folder = world(names)
    try:
        code, out, _ = run_cli(["--check", "--root", folder])
        report, audit_code = OOS.audit(folder)
        ok = (code == 0 and audit_code == 0 and report["verdict"] == "OK"
              and report["refused"] == [] and report["one_offs"] == 2
              and report["max_round"] == 2583)
        if not ok:
            print("  measured: code=%r verdict=%r refused=%r one_offs=%r "
                  "max_round=%r" % (code, report["verdict"],
                                    report["refused"], report["one_offs"],
                                    report["max_round"]), flush=True)
    finally:
        cleanup(folder)
    check(ok, "AC-OOS3 export_R2431 and fold_R2583b count as one-offs below "
          "the freeze and are not refused; the four permanent modules are not "
          "one-offs at all")


def ac_oos4():
    """AC-OOS4: the real tree reads OK, and its numbers are measurements."""
    report, code = OOS.audit(ROOT)
    cli_code, cli_out, _ = run_cli(["--check", "--root", ROOT])
    counted = re.search(r"one_offs=(\d+)", cli_out)
    maxed = re.search(r"max_round=(\d+)", cli_out)
    agrees = (counted is not None and maxed is not None
              and int(counted.group(1)) == report["one_offs"]
              and int(maxed.group(1)) == report["max_round"])
    ok = (code == 0 and cli_code == 0 and report["verdict"] == "OK"
          and report["refused"] == [] and report["one_offs"] > 0
          and report["max_round"] < report["freeze"] and agrees)
    print("  measured: one_offs=%d max_round=%d freeze=%d refused=%d"
          % (report["one_offs"], report["max_round"], report["freeze"],
             len(report["refused"])), flush=True)
    check(ok, "AC-OOS4 the live tree reads OK at rc=0 with every one-off "
          "below the freeze, and the CLI prints the same two numbers the "
          "library derives")


def ac_oos5():
    """AC-OOS5: an empty scope is NONE, not CLEAN, and codes are distinct."""
    empty = world(["state_append.py", "export_round.py"])
    try:
        none_code, none_out, _ = run_cli(["--check", "--root", empty])
        none_ok = none_code == 0 and "verdict=NONE" in none_out
        missing_code, _, _ = run_cli(["--check", "--root",
                                      os.path.join(empty, "no-such-tree")])
        scope_code, _, _ = run_cli(["--check", "--root", empty,
                                     "--scope", "no/such/scope"])
        flags_code, _, flags_err = run_cli(["--check", "--nonsense"])
        freeze_code, _, _ = run_cli(["--check", "--root", empty, "--freeze",
                                     "not-a-number"])
        ok = (none_ok and missing_code == 3 and scope_code == 3
              and flags_code == 5 and freeze_code == 5
              and "E_OOS_BAD_FLAGS" in flags_err)
        if not ok:
            print("  measured: none=%r/%r missing=%r scope=%r flags=%r "
                  "freeze=%r" % (none_ok, none_code, missing_code, scope_code,
                                 flags_code, freeze_code), flush=True)
    finally:
        cleanup(empty)
    check(ok, "AC-OOS5 an empty scope reads NONE at rc=0 (nothing to check is "
          "not everything clean), a missing root or scope reads 3, and bad "
          "flags read 5")


def ac_oos6():
    """AC-OOS6: registered with this exact criteria count."""
    runner_text = io.open(RUNNER, encoding="utf-8").read()
    pattern = re.compile(
        r"\(" + json.dumps(LABEL) + r",\s*\n\s*os\.path\.join\([^)]*\),\s*"
        r"(\d+)\)")
    match = pattern.search(runner_text)
    registered = match is not None
    declared = int(match.group(1)) if registered else -1
    ok = registered and declared == EXPECTED_CRITERIA
    if not ok:
        print("  measured: registered=%r declared=%r expected=%r"
              % (registered, declared, EXPECTED_CRITERIA), flush=True)
    check(ok, "AC-OOS6 the registry declares this suite at %d criteria"
          % EXPECTED_CRITERIA)


def main():
    print("one-off round scripts suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_oos1()
    ac_oos2()
    ac_oos3()
    ac_oos4()
    ac_oos5()
    ac_oos6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
