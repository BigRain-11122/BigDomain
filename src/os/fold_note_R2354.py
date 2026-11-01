"""fold_note_R2354 - append the fold-repair items the closeout could not know.

The closeout writes the window items and folds; the fold is what CREATES the
damage this note records, so it cannot describe it beforehand. Written with
the same canon and read-back proof as every other state write.
"""

import io
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_io as SIO  # noqa: E402

STATE = os.path.join(ROOT, "src", "os", "state.json")

ITEMS = [
    "R2354 fold repair disclosed (measured, not assumed): the closeout fold "
    "(638) was chosen on a tokens line at log position 8 and it cut the "
    "R2344 round block in half - that round line and its ledger line moved "
    "into the archive while the D-20260930-19 decision gate and the AC-RWH1 "
    "honest-disclosure item stayed live, so ledger_lines read "
    "rounds_without_ledger=2344 and three ledger suites (AC-LGR8, AC-LGA7/"
    "AC-LGA8, AC-LGB8) plus os-residue-triage AC-RTR6 went red on that single "
    "root cause. Repaired at the birth site of the damage rather than by "
    "relabelling a gate: fold 639 moved exactly those two orphaned items "
    "(log lines 2..3) verbatim into the same monthly archive, preop predicted "
    "73647B equal to the measured 73647B, margin 4853B, tokens_missing empty "
    "after the summary named both D-20260930-19 and AC-RWH1 so no token could "
    "be lost. The four suites then re-read 8/8, 8/8, 8/8 and 6/6, and "
    "ledger_lines reads VERDICT CLEAN with rounds_without_ledger=none.",
    "R2354 fold-created residue spliced by name, not by hand: fold 638 left "
    "round R2343 stamped and untriaged (the fold-creates-residue law first "
    "measured at R2311), so the shipped append channel declared it at its "
    "measured status DELIVERED (its ledger line and its done row are on disk) "
    "with declared_by=R2354 until=R2363 - 207 -> 208 entries, 61827B -> "
    "62150B, delta +323, read back TRIAGED 208/208. Disclosed honestly: the "
    "first attempt used the triage CLI (which has no --append) and the second "
    "used a flag the writer does not carry (--execute; this writer appends by "
    "default and dry-runs on --dry-run), so both refusals were THIS WINDOW's "
    "own argument errors and neither touched a byte.",
]


def main(argv):
    execute = "--execute" in argv
    with io.open(STATE, "r", encoding="utf-8") as handle:
        state = json.load(handle)
    state["log"] = state["log"] + ITEMS
    payload = json.dumps(state, ensure_ascii=False, indent=2, sort_keys=False)
    data = SIO.canon(payload).encode("utf-8")
    print("STATE items=%d bytes=%d" % (len(state["log"]), len(data)))
    if not execute:
        print("DRY RUN: pass --execute to write")
        return 0
    folder = os.path.dirname(os.path.abspath(STATE))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".state_R2354n_")
    try:
        with os.fdopen(handle, "wb") as sink:
            sink.write(data)
            sink.flush()
            os.fsync(sink.fileno())
        os.replace(temp, STATE)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise
    with io.open(STATE, "rb") as back:
        landed = back.read()
    ok = landed == data
    print("STATE READBACK ok=%s" % ok)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))