"""fold_R2350 - fold the oldest log window so the round fits the waterline.

The closeout appended its five lines and state_io canon-wrote the file to
82816B, which is 4316B over the 78500B gate. As in fold_R2341 the window end
is constrained to a ROUND BOUNDARY: the last folded item must be a
'tokens: local=' ledger line, which is the last line a round block writes, so
no block is cut in half (the open fold-block-boundary debt row still owns the
general law; this script refuses to fold across a boundary it cannot see).
Dry run by default; --execute appends to the archive and rewrites state.json.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")

sys.path.insert(0, BASE)
import state_fold as SF  # noqa: E402

FOLD_NO = 636
RESERVE = 200


def main(argv):
    raw = io.open(STATE, "rb").read()
    state = json.loads(raw.decode("utf-8"))
    print("state=%dB log_items=%d" % (len(raw), len(state["log"])))
    chosen = None
    for end in range(3, 30):
        if " tokens: local=" not in state["log"][end - 1]:
            print("skip end=%d (not a round boundary)" % end)
            continue
        window = state["log"][0:end]
        tokens = set()
        for line in window:
            tokens |= set(SF.PAT.findall(line))
        summary = ("Fold R2350: log lines 1..%d folded verbatim into the "
                   "archive so the closeout fits the waterline; window ends "
                   "on a tokens ledger line (round boundary); window "
                   "tokens: %s" % (end, " ".join(sorted(tokens))))
        plan, _text = SF.plan_fold(raw, state, 1, end, summary,
                                   reserve=RESERVE)
        print("candidate end=%d predicted=%dB gate_ok=%r missing=%d"
              % (end, plan["predicted_bytes"], plan["gate_ok"],
                 len(plan["tokens_missing"])))
        if plan["gate_ok"] and not plan["tokens_missing"]:
            chosen = (end, summary)
            break
    if not chosen:
        raise SystemExit("E_R2350_NO_WINDOW")
    if "--execute" not in argv:
        print("DRY RUN - wrote nothing")
        return 0
    result = SF.fold(ROOT, "R2350", FOLD_NO, 1, chosen[0], chosen[1],
                     reserve=RESERVE, execute=True)
    print("fold=%d window=1..%d predicted=%sB post=%sB margin=%s"
          % (FOLD_NO, chosen[0], result.get("predicted_bytes"),
             result.get("post_bytes", result.get("actual_bytes")),
             result.get("margin")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))