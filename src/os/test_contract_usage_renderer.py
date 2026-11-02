"""contract_usage_renderer suite (R2373).

Criteria AC-CUR1..AC-CUR6 were pinned inside the R2366 tech seed row of
state/queue/tech.md:419 BEFORE this code existed.

What this proves: the runner contract had TWO formatters - the guard's
two-line usage block and the wire's one-line house line - so a third tool
would have made three. One module now owns the vocabulary (which keys are
required, how a flag list is spelled, and the honest "(none)") while the two
already-published texts stay byte-identical. Patching the guard's exported
renderer moves BOTH CLIs, which is the only proof that neither writes its own
format string any more.

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
import contract_usage_renderer as CUR  # noqa: E402
import runner_arg_guard as G  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "contract_usage_renderer.py")
GUARD = os.path.join(BASE, "runner_arg_guard.py")
WIRE = os.path.join(BASE, "battery_followup_help_wire.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-contract-usage-renderer"
WIRED_EXPECT = '"test_contract_usage_renderer.py"), 6),'

# The two texts R2366 published, measured on this tree BEFORE the collapse
# and unchanged after it.
PUBLISHED_GUARD = "usage: reconcile_all.py [evidence_log_path]\n" \
                  "known flags: (none)"
PUBLISHED_HOUSE = \
    "house contract: reconcile_all.py [evidence_log_path] flags=(none)"
PUBLISHED_WIRE_HEAD = ("usage: battery_followup.py --evidence EVIDENCE "
                       "--label LABEL --root ROOT --round ROUND --dry-run "
                       "--json [--help]")

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


def contract(**over):
    base = {"name": "tool.py", "positional_label": "evidence_log_path",
            "known_flags": ("--a", "--b")}
    base.update(over)
    return base


def ac_cur1():
    """One owner: patching the guard's renderer moves BOTH CLIs."""
    import contextlib

    real_usage = G.usage_text
    real_line = G.contract_line
    moved_guard = ""
    moved_wire = ""
    try:
        G.usage_text = lambda c: "PATCHED-GUARD-BLOCK"
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            G.main(["prog", "--help"])
        moved_guard = buffer.getvalue().replace("\r\n", "\n")
        G.usage_text = real_usage
        G.contract_line = lambda c: "PATCHED-HOUSE-LINE"
        moved_wire = HW.usage_text()
        G.contract_line = real_line
    finally:
        G.usage_text = real_usage
        G.contract_line = real_line
    guard_src = read(GUARD)
    wire_src = read(WIRE)
    # No second format string for THIS shape anywhere else in the tree: the
    # guard writes none and the wire writes none, they only call the module.
    # (The wire's own report line spells a comma-joined flag list and is a
    # different question, so only the contract-block shape is pinned here.)
    guard_no_format = ("known flags: %s" not in guard_src
                       and '"usage: %s [%s]' not in guard_src)
    wire_no_format = ("house contract:" not in wire_src
                      and "[%s] flags=%s" not in wire_src)
    ok = ("PATCHED-GUARD-BLOCK" in moved_guard
          and "PATCHED-HOUSE-LINE" in moved_wire
          and guard_no_format and wire_no_format)
    if not ok:
        print("  measured: guard=%r wire=%r no_format=%r/%r"
              % ("PATCHED-GUARD-BLOCK" in moved_guard,
                 "PATCHED-HOUSE-LINE" in moved_wire,
                 guard_no_format, wire_no_format), flush=True)
    check(ok, "AC-CUR1 renderer owned by the module; patching it moves both "
              "CLIs and no second format string is written")


def ac_cur2():
    """Every already-published line stays byte-identical to R2366."""
    guard_out = run_cli(GUARD, ["--help"])
    wire_out = run_cli(WIRE, ["--help"])
    guard_lib = G.usage_text(G.load_contract())
    wire_block = HW.usage_text()
    ok = (guard_out[0] == 0
          and guard_lib == PUBLISHED_GUARD
          and PUBLISHED_GUARD in guard_out[1]
          and PUBLISHED_HOUSE in wire_block.splitlines()
          and PUBLISHED_WIRE_HEAD in wire_block.splitlines()
          and wire_out[0] == 0
          and PUBLISHED_HOUSE in wire_out[1])
    if not ok:
        print("  measured: lib=%r house=%r head=%r"
              % (guard_lib, PUBLISHED_HOUSE in wire_block.splitlines(),
                 PUBLISHED_WIRE_HEAD in wire_block.splitlines()), flush=True)
    check(ok, "AC-CUR2 both published texts byte-identical; the collapse adds "
              "no new wording")


def ac_cur3():
    """A contract with a missing key refuses with its own code."""
    codes = []
    for key in CUR.KEYS:
        short = dict(contract())
        short.pop(key)
        try:
            CUR.block(short)
            codes.append("NO-RAISE")
        except CUR.ContractUsageError as exc:
            codes.append(exc.code)
    bad_flags = None
    try:
        CUR.inline(contract(known_flags="--a --b"))
    except CUR.ContractUsageError as exc:
        bad_flags = exc.code
    # The wire keeps its own published refusal code on the same input.
    real_load = HW.load_runner_contract
    wire_code = None
    try:
        HW.load_runner_contract = lambda path=None: {"name": "x"}
        try:
            HW.usage_text()
        except HW.HelpWireError as exc:
            wire_code = exc.code
    finally:
        HW.load_runner_contract = real_load
    expected = [CUR.E_CUR_MISSING + key.upper() for key in CUR.KEYS]
    ok = (codes == expected and bad_flags == CUR.E_CUR_BAD_FLAGS
          and wire_code == HW.E_BFH_NO_CONTRACT)
    if not ok:
        print("  measured: codes=%r bad_flags=%r wire=%r"
              % (codes, bad_flags, wire_code), flush=True)
    check(ok, "AC-CUR3 a missing key refuses with its own code instead of "
              "rendering a partial block")


def ac_cur4():
    """An empty flag set reads the honest '(none)' in both shapes."""
    empty = contract(known_flags=())
    block_empty = CUR.block(empty)
    inline_empty = CUR.inline(empty)
    full = CUR.block(contract())
    ok = (block_empty.splitlines()[-1] == "known flags: (none)"
          and inline_empty.endswith("flags=(none)")
          and "known flags: --a --b" in full
          and CUR.flag_text(empty) == "(none)")
    if not ok:
        print("  measured: block=%r inline=%r" % (block_empty, inline_empty),
              flush=True)
    check(ok, "AC-CUR4 an empty flag set renders (none) rather than a blank")


def ac_cur5():
    """Wire exit codes 0/2/5 and a byte-stable --json on both CLIs."""
    help_run = run_cli(WIRE, ["--help"])
    unknown = run_cli(WIRE, ["--nonsense"])
    no_args = run_cli(WIRE, [])
    wire_a = run_cli(WIRE, ["--json", "--help"])
    wire_b = run_cli(WIRE, ["--json", "--help"])
    guard_a = run_cli(GUARD, ["--json", "--dry-run"])
    guard_b = run_cli(GUARD, ["--json", "--dry-run"])
    payload = json.loads(guard_a[1].strip())
    keys_ok = sorted(payload.keys()) == sorted(G.JSON_KEYS)
    wire_tail_ok = wire_a[1].rstrip().endswith("}")
    ok = (help_run[0] == 0 and unknown[0] == 2 and no_args[0] == 5
          and wire_a[1] == wire_b[1] and wire_tail_ok
          and guard_a[1] == guard_b[1] and keys_ok
          and guard_a[0] == 2)
    if not ok:
        print("  measured: %r %r %r stable=%r/%r keys=%r"
              % (help_run[0], unknown[0], no_args[0],
                 wire_a[1] == wire_b[1], guard_a[1] == guard_b[1],
                 keys_ok), flush=True)
    check(ok, "AC-CUR5 wire exits 0/2/5 and both CLIs keep a byte-stable "
              "--json over pinned keys")


def ac_cur6():
    """ASCII, stdlib only, no clock, no network, and the sections still run."""
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
    check(ok, "AC-CUR6 pure ASCII, stdlib only, no clock, no network, the four "
              "follow-up sections intact, one runner entry at 6 criteria")


def main():
    print("SUITE contract_usage_renderer (R2373) criteria=%d"
          % EXPECTED_CRITERIA, flush=True)
    for name, fn in (("AC-CUR1", ac_cur1), ("AC-CUR2", ac_cur2),
                     ("AC-CUR3", ac_cur3), ("AC-CUR4", ac_cur4),
                     ("AC-CUR5", ac_cur5), ("AC-CUR6", ac_cur6)):
        fn()
    total = PASSES + FAILS
    if FAILS == 0 and PASSES == EXPECTED_CRITERIA:
        print("SUITE PASS %d/%d" % (PASSES, EXPECTED_CRITERIA), flush=True)
        return 0
    print("SUITE FAIL %d/%d" % (PASSES, total), flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())