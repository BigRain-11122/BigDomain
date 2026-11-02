"""board_R2371 - stamp the claimed tech row and seed one measured gap row.

Two writes, both predicted before the write and read back after it:
  1. state/queue/tech.md row AC-RWAG1 (the claimed R2359 seed) gets its
     [done 2026-11-02 R2371] marker; the bracket payload stays inside the
     60-character stamp law.
  2. one REAL gap row is appended at the tail, pre-registering
     AC-RWGP1..AC-RWGP6 from this window's own measurement, so the tech floor
     is refilled by a measured gap rather than by filler.

ASCII source, one atomic replace per file, no clock, no network.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

MARK_OLD = "\n- [ ] P2 tech seed (R2359"
MARK_NEW = "\n- [x] [done 2026-11-02 R2371] P2 tech seed (R2359"

GAP = (
    "- [ ] P2 tech seed (R2371, from this window own measured gap): "
    "`review_window_guard_parity` - the same declarations list is now read by "
    "two faces and nothing measures that they agree: "
    "`review_window_wire.window_report` refuses a rewinding list with "
    "E_RWHW_DECL_HISTORY (the DECLARED path) and "
    "`review_window_wire_argument_guard.guard` refuses the same file with the "
    "same code (the ARGUMENT path), but each was proved on its own fixtures "
    "and the pair has never been run over one declaration to say AGREES or "
    "DISAGREES. Product: one parity reader that hands the same file to both "
    "faces, reports the two verdicts side by side, and reads PARITY-DISAGREES "
    "naming both codes when they diverge, so a future edit to either law "
    "cannot silently split the two paths. Criteria AC-RWGP1..AC-RWGP6 "
    "pre-registered HERE BEFORE any code: AC-RWGP1 both faces are IMPORTED "
    "and patching either one moves the parity report, so no third reading of "
    "the declarations list is written; AC-RWGP2 a rewinding declaration reads "
    "PARITY-AGREES with both faces naming E_RWHW_DECL_HISTORY; AC-RWGP3 a "
    "monotonic declaration reads PARITY-AGREES with the declared window "
    "carried from the wire and the argument guard reporting its own history "
    "word, the two being different questions and not a disagreement; AC-RWGP4 "
    "a patched divergence on either side reads PARITY-DISAGREES naming both "
    "codes and writes nothing; AC-RWGP5 CLI codes 0/2/3/5 with a byte-stable "
    "--json over a pinned key order; AC-RWGP6 pure ASCII, stdlib only, zero "
    "network, no clock, read-only, plus its own reconcile label. Five anchors "
    "zero-occupancy at HEAD 2026-11-02: review_window_guard_parity, AC-RWGP, "
    "E_RWGP, os-review-window-guard-parity, "
    "test_review_window_guard_parity.\n"
)


def read_bytes(path):
    with io.open(path, "rb") as handle:
        return handle.read()


def write_atomic(path, data):
    tmp = path + ".tmp-R2371"
    with io.open(tmp, "wb") as handle:
        handle.write(data)
    os.replace(tmp, path)
    return read_bytes(path)


def main():
    before = read_bytes(QUEUE)
    text = before.decode("utf-8")
    hits = text.count(MARK_OLD)
    if hits != 1:
        print("REFUSED expected exactly one claimable R2359 row, found %d"
              % hits)
        return 2
    stamped = text.replace(MARK_OLD, MARK_NEW, 1)
    predicted = len(before) + (len(MARK_NEW) - len(MARK_OLD))
    if len(stamped.encode("utf-8")) != predicted:
        print("REFUSED stamp prediction mismatch")
        return 2
    after = write_atomic(QUEUE, stamped.encode("utf-8"))
    if len(after) != predicted:
        print("REFUSED stamped read-back size")
        return 3

    before2 = after
    tail = before2.decode("utf-8")
    if not tail.endswith("\n"):
        tail += "\n"
    seeded = tail + GAP
    predicted2 = len(before2) + len(GAP.encode("utf-8"))
    if len(seeded.encode("utf-8")) != predicted2:
        print("REFUSED seed prediction mismatch")
        return 2
    final = write_atomic(QUEUE, seeded.encode("utf-8"))
    if len(final) != predicted2 or not final.decode("utf-8").endswith(GAP):
        print("REFUSED seed read-back")
        return 3

    print("STAMPED row AC-RWAG1 payload=%d chars bytes %d -> %d"
          % (len("done 2026-11-02 R2371"), len(before), len(after)))
    print("SEEDED review_window_guard_parity bytes %d -> %d"
          % (len(before2), len(final)))
    return 0


if __name__ == "__main__":
    sys.exit(main())