"""fold_R2335 - fold the oldest log window so the round fits the waterline.

The closeout appended its five lines and state_io canon-fixed the file to
78705B, which is 205B over the 78500B gate; this folds a window of the oldest
log items verbatim into the monthly archive (state_fold owns the law) and
proves the predicted byte count equals the measured one.
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

FOLD_NO = 624
RESERVE = 200


def main(argv):
    raw = io.open(STATE, "rb").read()
    state = json.loads(raw.decode("utf-8"))
    print("state=%dB log_items=%d" % (len(raw), len(state["log"])))
    chosen = None
    for end in range(3, 16):
        window = state["log"][0:end]
        tokens = set()
        for line in window:
            tokens |= set(SF.PAT.findall(line))
        summary = ("Fold R2335: log lines 1..%d folded verbatim into the "
                   "archive so the closeout fits the waterline; window "
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
        raise SystemExit("E_R2335_NO_WINDOW")
    if "--execute" not in argv:
        print("DRY RUN - wrote nothing")
        return 0
    result = SF.fold(ROOT, "R2335", FOLD_NO, 1, chosen[0], chosen[1],
                     reserve=RESERVE, execute=True)
    print("fold=%d window=1..%d predicted=%sB post=%sB margin=%s"
          % (FOLD_NO, chosen[0], result.get("predicted_bytes"),
             result.get("post_bytes", result.get("actual_bytes")),
             result.get("margin")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))