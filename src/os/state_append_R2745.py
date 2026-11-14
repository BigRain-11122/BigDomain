"""state_append_R2745 - restore the R2742 ledger line that its closeout never
wrote, through the canonical writer, in its own chronological position.

The live window carried six R2742 narrative lines with no R2742 tokens line
and the archive carried none either, so five ledger suites read red on the
real tree (rounds_without_ledger [2742]). This script only restores the
missing line; the estimate marker and the api_reason text say plainly that
R2745 reconstructed it.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import state_io  # noqa: E402

STATE = os.path.join(BASE, "state.json")
TICK = 2745

LEDGER = (
    "R2742 tokens: local=~13k api=0 api_reason=product window RECONSTRUCTED AT R2745 "
    "because the R2742 closeout never wrote its ledger line - six R2742 narrative lines "
    "sit live with no tokens line and the archive holds none, which reddened five ledger "
    "suites (rounds_without_ledger 2742); local is therefore an ESTIMATE from that window "
    "own recorded actions (one blind-spot re-measurement, one face, one six-criteria suite, "
    "two evidence legs, one live reading on the real document, one registry count by import, "
    "one matrix restamp, one board close and three debt calls) and api=0 is certain because "
    "its own disclosures record zero cloud calls and zero external API touches"
)


def main():
    raw = state_io.read_raw(STATE)
    data = state_io.parse(state_io.decode(raw))
    log = data["log"]
    if any(l.startswith("R2742 tokens:") for l in log):
        sys.stdout.write("NOOP existing R2742 ledger line\n")
        return 0
    last = max(i for i, l in enumerate(log)
               if l.startswith("R2742") or " R2742 " in l[:40])
    before = len(log)
    log.insert(last + 1, LEDGER)
    data["tick"] = TICK
    state_io.write_document(STATE, data)
    back = json.load(io.open(STATE, encoding="utf-8"))
    bl = back.get("log") or []
    ok = (back.get("tick") == TICK
          and len(bl) == before + 1
          and bl[last + 1] == LEDGER)
    sys.stdout.write("RESTORED tick=%s log %d->%d at=%d ok=%s\n"
                     % (back.get("tick"), before, len(bl), last + 1, ok))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
