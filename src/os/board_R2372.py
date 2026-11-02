"""board_R2372 - stamp the claimed row and seed ONE measured gap row.

The claimed row is state/queue/tech.md:418 (prefix AC-RTRI1,
residue_triage_repin_idempotent), whose AC-RTRI1..AC-RTRI6 were pinned there at
R2363 BEFORE any code. The seed is the seam this window measured on the live
tree: the shipped `residue_triage_repin` CLI still reports PLANNED over a
composition identical to the file, and only the new wire knows NOOP, so the
same act now has two answers.

One atomic write each, with the byte count predicted before the write and the
result read back; no temp residue.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
STEMP = ".tmp-board-r2372"
STAMP = "[done 2026-11-02 R2372]"
ROUND = 2372

SEED = (
    "- [ ] P2 tech seed (R2372, from this window own measured seam): "
    "`src/os/repin_noop_parity` - the re-pin now has a NOOP in ONE module and "
    "not in the tool operators run. Measured this window: "
    "`residue_triage_repin_idempotent.decide` reads NOOP when the composed "
    "declaration equals the file on disk, but `residue_triage_repin.py "
    "--execute` still reports PLANNED over that same composition and rewrites "
    "the identical bytes as PINNED, so the shipped CLI and the wire give two "
    "answers to one question and a caller cannot tell which law ran. Product: "
    "one law both faces ask - the shipped CLI routes its plan through the "
    "byte comparison (or grows the same NOOP verdict), so PLANNED, PINNED and "
    "NOOP mean the same thing whichever entry point is used and the parity is "
    "measured over ONE declaration rather than asserted. Criteria "
    "AC-RNP1..AC-RNP6 pre-registered HERE BEFORE any code: AC-RNP1 the "
    "shipped CLI reads NOOP over an already-pinned declaration with the file "
    "digest unchanged; AC-RNP2 the shipped CLI's executed output and the "
    "wire's are byte-identical for every non-NOOP path, including refusals "
    "and their exit codes; AC-RNP3 the two CLIs agree on ONE declaration run "
    "at the same instant, reading AGREES or naming the first field that "
    "differs; AC-RNP4 the --json key order stays PLAN_KEYS on both and NOOP "
    "adds no key; AC-RNP5 no second composition and no second writer is "
    "created - the shipped module keeps its own write primitive and the "
    "comparison is imported, not copied; AC-RNP6 pure ASCII, stdlib only, "
    "zero network, no clock, wired into the registry with its own suite. "
    "Five anchors zero-occupancy at HEAD 2026-11-02: repin_noop_parity, "
    "AC-RNP, E_RNP, os-repin-noop-parity, test_repin_noop_parity.\n"
)


def plan(text):
    lines = text.split("\n")
    for index, line in enumerate(lines):
        if line.startswith("- [ ] P2 tech seed (R2363") \
                and "residue_triage_repin_idempotent" in line:
            stamped = "- [x] " + STAMP + " " + line[len("- [ ] "):]
            lines[index] = stamped
            break
    else:
        raise SystemExit("E_BOARD_NO_ROW: the claimed row was not found")
    body = "\n".join(lines)
    if not body.endswith("\n"):
        body += "\n"
    body += SEED
    return body


def main():
    with io.open(QUEUE, "r", encoding="utf-8", newline="") as handle:
        before = handle.read()
    body = plan(before)
    predicted = len(body.encode("utf-8"))
    temp = QUEUE + STEMP
    with io.open(temp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    os.replace(temp, QUEUE)
    sized = os.path.getsize(QUEUE)
    with io.open(QUEUE, "r", encoding="utf-8", newline="") as handle:
        after = handle.read()
    residue = [name for name in os.listdir(os.path.dirname(QUEUE))
               if STEMP.strip(".") in name]
    stamp_ok = ("- [x] " + STAMP) in after and "- [ ] P2 tech seed (R2363" \
        not in after
    seed_ok = "AC-RNP6" in after and "repin_noop_parity" in after
    print("BOARD R%d before=%dB predicted=%d measured=%d stamp=%s seed=%s "
          "residue=%d" % (ROUND, len(before.encode("utf-8")), predicted,
                          sized, stamp_ok, seed_ok, len(residue)))
    return 0 if (sized == predicted and stamp_ok and seed_ok
                 and not residue) else 1


if __name__ == "__main__":
    sys.exit(main())