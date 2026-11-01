"""fold_R2341 - fold the oldest log window so the round fits the waterline.

The closeout appended its five lines and state_io canon-fixed the file to
85761B, which is 7261B over the 78500B gate. This differs from the R2335
predecessor in one place only: the window end is constrained to a ROUND
BOUNDARY, i.e. the last folded item must be a 'tokens:' ledger line, which is
the last line a round block writes. The open fold-block-boundary debt row says
a window chosen by count alone can cut a round in half; this window does not
fix the law in state_fold (that belongs to the row that touches folds) but it
refuses to fold across a boundary it cannot see. Dry run by default.
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

FOLD_NO = 629
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
        summary = ("Fold R2341: log lines 1..%d folded verbatim into the "
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
        raise SystemExit("E_R2341_NO_WINDOW")
    if "--execute" not in argv:
        print("DRY RUN - wrote nothing")
        return 0
    result = SF.fold(ROOT, "R2341", FOLD_NO, 1, chosen[0], chosen[1],
                     reserve=RESERVE, execute=True)
    print("fold=%d window=1..%d predicted=%sB post=%sB margin=%s"
          % (FOLD_NO, chosen[0], result.get("predicted_bytes"),
             result.get("post_bytes", result.get("actual_bytes")),
             result.get("margin")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))