"""R2331 top-up fold: the six log items crossed the waterline by 106B.

state.json measured 78606B against the 78500B gate after the closeout items
landed, so one more small window is folded (whole items only, chosen from the
real plan so the post size clears the gate with a margin). The summary carries
every token of the window, the archive append is prefix-proved by state_fold
itself, and nothing else is written. Pure ASCII, stdlib only.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_fold as SF  # noqa: E402

STATE = os.path.join(ROOT, "src", "os", "state.json")
FOLD_NO = 622
RESERVE = 7000


def main():
    raw = io.open(STATE, "rb").read()
    state = json.loads(raw.decode("utf-8"))
    if any(line.startswith("Fold R2331 top-up:") for line in state["log"]):
        print("top-up already applied")
        return
    chosen = None
    for end in range(2, 12):
        window = state["log"][1:end]
        tokens = set()
        for line in window:
            tokens |= set(SF.PAT.findall(line))
        summary = ("Fold R2331 top-up: log lines 2..%d folded verbatim so the "
                   "closeout clears the waterline; window tokens: %s"
                   % (end, " ".join(sorted(tokens))))
        plan, _text = SF.plan_fold(raw, state, 2, end, summary,
                                   reserve=RESERVE)
        print("candidate end=%d predicted=%dB gate_ok=%r missing=%d margin=%d"
              % (end, plan["predicted_bytes"], plan["gate_ok"],
                 len(plan["tokens_missing"]), plan["margin"]))
        if plan["gate_ok"] and not plan["tokens_missing"]:
            chosen = (end, summary)
            break
    if not chosen:
        raise SystemExit("E_TOPUP_NO_WINDOW")
    result = SF.fold(ROOT, "R2331", FOLD_NO, 2, chosen[0], chosen[1],
                     reserve=RESERVE, execute=True)
    print("fold=%d window=2..%d predicted=%sB"
          % (FOLD_NO, chosen[0], result.get("predicted_bytes")))


if __name__ == "__main__":
    main()