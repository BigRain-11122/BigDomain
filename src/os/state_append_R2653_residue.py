"""state_append_R2653_residue - one honest correction of a drifting reading.

The R2653 receipt line recorded residue_triage --check --round R2653 as
unmatched=0 at the moment the declaration landed. Re-read at the very end of
this window it says unmatched=1, because R2653 has since left the live residue
set - the same shape the two inherited entries already carry. Verdict stays
TRIAGED and nothing is hidden.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import general_writer_dialect_audit as GWDA  # noqa: E402

STATE = os.path.join(REPO, "src", "os", "state.json")

LINES = [
    "R2653 RESIDUE RE-READ, disclosed rather than smoothed: the receipt line"
    " above recorded unmatched=0 because R2653 was still in the live residue"
    " set when the declaration landed; re-read on the final committed tree it"
    " reads declaration=PINNED residue=1 triaged=1 untriaged=0 unmatched=1"
    " verdict=TRIAGED, the unmatched entry being this round own DELIVERED row"
    " after it left the live set - the same shape the inherited entries carry,"
    " and the gate verdict is TRIAGED. No value was edited to make the earlier"
    " number true.",
]


def main():
    with io.open(STATE, "r", encoding="utf-8") as fh:
        raw = fh.read()
    state = json.loads(raw)
    for line in LINES:
        state["log"].append(line)
    text = json.dumps(state, indent=1, ensure_ascii=False)
    payload = GWDA.payload_for(STATE, text)
    before = len(raw.encode("utf-8"))
    with io.open(STATE, "wb") as fh:
        fh.write(payload)
    with io.open(STATE, "rb") as fh:
        check = fh.read()
    reread = json.loads(check.decode("utf-8"))
    ok = len(reread["log"]) == len(state["log"])
    print("APPEND-CORRECTION tick=%d bytes %d -> %d readback=%s"
          % (reread["tick"], before, len(check), "ok" if ok else "FAILED"))
    return 0 if ok else 4


if __name__ == "__main__":
    sys.exit(main())
