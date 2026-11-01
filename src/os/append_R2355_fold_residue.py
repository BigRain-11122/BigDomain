"""append_R2355_fold_residue - one log item for the fold's own side effect.

Fold 640 moved three round blocks into the archive and left R2345, R2346 and
R2348 untriaged (the fold-creates-residue law). The shipped single-entry
append refuses a multi-round splice by design, so the three were composed
through that module's own reader, shape, composer and judge in ONE atomic
replace (src/os/splice_residue_R2355.py) and the batch capability was seeded
as a real gap row. This item is appended through state_io.canon so the
closeout keeps one writer and one canon.
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

ITEM = (
    "R2355 fold residue repaired at its birth site, not by relabelling a "
    "gate: fold 640 moved 27 items and left R2345, R2346 and R2348 untriaged "
    "in state/residue_triage.json (the fold-creates-residue law, measured "
    "again), which turned os-residue-triage red 5/6 while the four ledger "
    "suites re-read 8/8 each. The shipped residue_triage_append refuses a "
    "multi-round splice by DESIGN - plan() demands the file re-read TRIAGED "
    "after the single entry it adds - so the three rounds were composed "
    "through that module own declaration reader, entry shape, composer and "
    "judge in ONE atomic replace (src/os/splice_residue_R2355.py, a disclosed "
    "one-off): every round was declared at its MEASURED status DELIVERED "
    "(stamp_residue reads a closed-row hit for each), the judge read "
    "residue=[] disagrees=0 before any byte, the write predicted 62150B -> "
    "63026B and measured the same 63026B with no .tmp residue, and the "
    "read-back reads entries=211 verdict=TRIAGED untriaged=0; the suite then "
    "reads SUITE PASS 6/6. One REAL gap row was seeded from this measured "
    "pain (residue_triage_append_batch, AC-RTAB1..AC-RTAB6 pre-registered "
    "before any code, five anchors zero-occupancy at HEAD 2026-11-02), and "
    "the gauge reads FLOOR-MET main 5/5 tech 11/10 explore 10/10."
)

execute = "--execute" in sys.argv
state = json.load(io.open(STATE, "r", encoding="utf-8"))
state["log"] = state["log"] + [ITEM]
payload = json.dumps(state, ensure_ascii=False, indent=2, sort_keys=False)
canon = SIO.canon(payload)
data = canon.encode("utf-8")
print("STATE tick=%d log_items=%d bytes=%d"
      % (state["tick"], len(state["log"]), len(data)))
if not execute:
    print("DRY RUN: wrote nothing")
    raise SystemExit(0)
folder = os.path.dirname(os.path.abspath(STATE))
handle, temp = tempfile.mkstemp(dir=folder, prefix=".state_R2355b_")
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
ok = io.open(STATE, "rb").read() == data
print("STATE READBACK ok=%s" % ok)
raise SystemExit(0 if ok else 2)