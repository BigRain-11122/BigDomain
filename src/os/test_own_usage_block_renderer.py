"""own_usage_block_renderer suite (R2383).

Criteria AC-OUB1..AC-OUB6 were pinned inside the R2373 tech seed row of
state/queue/tech.md:429 BEFORE this code existed.

What this proves: R2373 gave the IMPORTED runner contract one owner, but a
tool's OWN argument block still had none - runner_arg_guard.guard_usage()
returned a hand-written literal and battery_followup_help_wire.usage_text()
composed its own flag line from format strings inside that module, so a third
tool had to copy one of those shapes. One module now owns that vocabulary
while both already-published own-blocks stay byte-identical. Patching the
renderer moves BOTH CLIs, which is the only proof that neither writes a
format string for its own block any more.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import io
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import battery_followup as BF  # noqa: E402
import battery_followup_help_wire as HW  # noqa: E402
import own_usage_block_renderer as OUB  # noqa: E402
import runner_arg_guard as G  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "own_usage_block_renderer.py")
GUARD = os.path.join(BASE, "runner_arg_guard.py")
WIRE = os.path.join(BASE, "battery_followup_help_wire.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-own-usage-block-renderer"
WIRED_EXPECT = '"test_own_usage_block_renderer.py"), 6),'

# The two own-blocks already published, measured on this tree BEFORE the
# collapse and unchanged after it (AC-OUB2).
PUBLISHED_GUARD = (
    "usage: runner_arg_guard.py [--json] [--] <runner argv ...>\n"
    "       runner_arg_guard.py --guard-help\n"
    "answers whether reconcile_all.py would accept that argv; "
    "exit 0 allowed/asked, 2 refused, 3 unreadable runner, 5 bad guard "
    "flags. A bare --help is forwarded to the runner as a QUESTION "
    "(exit 0), never swallowed by the guard.")
PUBLISHED_WIRE_HEAD = (
    "usage: battery_followup.py --evidence EVIDENCE --label LABEL "
    "--root ROOT --round ROUND --dry-run --json [--help]")

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


def read(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def run_cli(module, args):
    proc = subprocess.run([sys.executable, module] + list(args),
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          cwd=REPO)
    return (proc.returncode,
            proc.stdout.decode("utf-8", "replace").replace("\r\n", "\n"),
            proc.stderr.decode("utf-8", "replace"))


def ac_oub1():
    """One owner: patching the renderer moves BOTH own-blocks."""
    real_block = OUB.block
    moved_guard = ""
    moved_wire = ""
    try:
        OUB.block = lambda spec: "PATCHED-OWN-BLOCK"
        moved_guard = G.guard_usage()
        moved_wire = HW.usage_text()
    finally:
        OUB.block = real_block
    guard_src = read(GUARD)
    wire_src = read(WIRE)
    # No caller builds the block's own HEAD or its continuation indent any
    # more: the quoted literals that used to spell them are gone from both,
    # so every line comes from the module. (The guard's docstring may still
    # SHOW the published block, and the wire still passes the help token and
    # its footer prose as data - those are not format strings.)
    guard_no_format = ('"usage: ' not in guard_src
                       and '"       runner_arg_guard.py' not in guard_src)
    wire_no_format = ('"usage: ' not in wire_src
                      and '"%s %s" % (flag' not in wire_src)
    ok = (moved_guard == "PATCHED-OWN-BLOCK"
          and moved_wire == "PATCHED-OWN-BLOCK\n"
          and guard_no_format and wire_no_format)
    if not ok:
        print("  measured: guard=%r wire=%r no_format=%r/%r"
              % (moved_guard, moved_wire, guard_no_format, wire_no_format),
              flush=True)
    check(ok, "AC-OUB1 the renderer owns both own-blocks; patching it moves "
              "both CLIs and neither caller writes a format string")


def ac_oub2():
    """Every already-published own-block line stays byte-identical."""
    guard_out = run_cli(GUARD, ["--guard-help"])
    wire_out = run_cli(WIRE, ["--help"])
    guard_lib = G.guard_usage()
    wire_block = HW.usage_text()
    ok = (guard_out[0] == 0
          and guard_lib == PUBLISHED_GUARD
          and PUBLISHED_GUARD in guard_out[1]
          and PUBLISHED_WIRE_HEAD in wire_block.splitlines()
          and wire_block.endswith("\n")
          and PUBLISHED_WIRE_HEAD in wire_out[1])
    if not ok:
        print("  measured: lib_ok=%r head=%r rc=%r/%r"
              % (guard_lib == PUBLISHED_GUARD,
                 PUBLISHED_WIRE_HEAD in wire_block.splitlines(),
                 guard_out[0], wire_out[0]), flush=True)
    check(ok, "AC-OUB2 both published own-blocks byte-identical; the collapse "
              "adds no new wording")


def ac_oub3():
    """A missing metavar and an empty table each render their honest form."""
    no_metavar = OUB.head({"name": "tool.py", "takes": {"--x": ""}})
    no_flags = OUB.head({"name": "tool.py"})
    derived = OUB.head({"name": "tool.py",
                        "takes": {"--evidence": "evidence"}})
    ok = (no_metavar == "usage: tool.py --x"
          and no_flags == "usage: tool.py (none)"
          and derived == "usage: tool.py --evidence EVIDENCE")
    if not ok:
        print("  measured: no_metavar=%r no_flags=%r derived=%r"
              % (no_metavar, no_flags, derived), flush=True)
    check(ok, "AC-OUB3 a value flag with no metavar and a flagless table "
              "render their honest form rather than a partial line")


def ac_oub4():
    """An empty own-flag set renders '(none)'."""
    empty = OUB.block({"name": "tool.py", "takes": {}, "flags": (),
                       "prose": ()})
    wired_empty = OUB.block({"name": "tool.py", "takes": {},
                             "flags": {}, "help": "[--help]"})
    ok = (empty == "usage: tool.py (none)"
          and wired_empty.splitlines()[0] == "usage: tool.py [--help]")
    if not ok:
        print("  measured: empty=%r wired=%r" % (empty, wired_empty),
              flush=True)
    check(ok, "AC-OUB4 an empty own-flag set renders (none) rather than a "
              "blank line")


def ac_oub5():
    """Both CLIs keep their exit codes and a byte-stable --json."""
    help_run = run_cli(GUARD, ["--guard-help"])
    wire_help = run_cli(WIRE, ["--help"])
    wire_unknown = run_cli(WIRE, ["--nonsense"])
    wire_no_args = run_cli(WIRE, [])
    wire_a = run_cli(WIRE, ["--json", "--help"])
    wire_b = run_cli(WIRE, ["--json", "--help"])
    guard_a = run_cli(GUARD, ["--json", "--dry-run"])
    guard_b = run_cli(GUARD, ["--json", "--dry-run"])
    payload = json.loads(guard_a[1].strip())
    keys_ok = sorted(payload.keys()) == sorted(G.JSON_KEYS)
    ok = (help_run[0] == 0 and wire_help[0] == 0
          and wire_unknown[0] == 2 and wire_no_args[0] == 5
          and wire_a[1] == wire_b[1]
          and guard_a[1] == guard_b[1] and guard_a[0] == 2 and keys_ok)
    if not ok:
        print("  measured: %r %r %r %r stable=%r/%r keys=%r"
              % (help_run[0], wire_help[0], wire_unknown[0],
                 wire_no_args[0], wire_a[1] == wire_b[1],
                 guard_a[1] == guard_b[1], keys_ok), flush=True)
    check(ok, "AC-OUB5 both CLIs keep their exit codes and a byte-stable "
              "--json over pinned keys")


def ac_oub6():
    """ASCII, stdlib only, no clock, no network, four sections intact."""
    ascii_ok = True
    net_ok = True
    clock_ok = True
    for path in (MODULE, GUARD, WIRE):
        with io.open(path, "rb") as handle:
            raw = handle.read()
        if any(byte > 127 for byte in raw):
            ascii_ok = False
        source = raw.decode("utf-8")
        if any(token in source for token in
               ("socket", "urllib", "http.client", "requests")):
            net_ok = False
        if any(token in source for token in
               ("import time", "time.time", "datetime", "random")):
            clock_ok = False
    sections_ok = (tuple(getattr(BF, "SECTIONS", ()))
                   == ("matrix", "fingerprint", "profile", "census"))
    help_out = run_cli(WIRE, ["--help"])
    no_section_run = ("SECTION " not in help_out[1]
                      and "VERDICT " not in help_out[1])
    runner_src = read(RUNNER)
    wired = (('"%s"' % LABEL) in runner_src and WIRED_EXPECT in runner_src)
    ok = (ascii_ok and net_ok and clock_ok and sections_ok and no_section_run
          and wired)
    if not ok:
        print("  measured: ascii=%r net=%r clock=%r sections=%r wired=%r"
              % (ascii_ok, net_ok, clock_ok, sections_ok, wired), flush=True)
    check(ok, "AC-OUB6 pure ASCII, stdlib only, no clock, no network, the four "
              "follow-up sections intact, one runner entry at 6 criteria")


def main():
    print("SUITE own_usage_block_renderer (R2383) criteria=%d"
          % EXPECTED_CRITERIA, flush=True)
    for name, fn in (("AC-OUB1", ac_oub1), ("AC-OUB2", ac_oub2),
                     ("AC-OUB3", ac_oub3), ("AC-OUB4", ac_oub4),
                     ("AC-OUB5", ac_oub5), ("AC-OUB6", ac_oub6)):
        fn()
    total = PASSES + FAILS
    if FAILS == 0 and PASSES == EXPECTED_CRITERIA:
        print("SUITE PASS %d/%d" % (PASSES, EXPECTED_CRITERIA), flush=True)
        return 0
    print("SUITE FAIL %d/%d" % (PASSES, total), flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())