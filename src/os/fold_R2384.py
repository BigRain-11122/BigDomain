"""fold_R2384 - the waterline fold this window's closeout needs.

The state file stood at 78375B against the 78500B gate before this window's
items, and the R2384 log items take it to ~83280B, so the fold runs FIRST, at a
TRUE round-block boundary: window lines 1..26 end exactly where the R2377 block
begins, so the R2374, R2375 and R2376 blocks move whole (plus the R2383 fold
summary). The summary carries every token the window contained, computed from
the window itself rather than typed.

Source is ASCII, stdlib only, zero network.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_fold as SF  # noqa: E402

STATE = os.path.join(REPO, "src", "os", "state.json")
ROUND = "R2384"
FOLD_NO = "646"
WINDOW_START = 1
WINDOW_END = 26

LEAD = (
    "Fold R2384: log lines 1..26 folded verbatim into the archive (the R2383 "
    "fold summary and the whole R2374, R2375 and R2376 round blocks), cut AFTER "
    "the R2376 block at a TRUE round-block boundary so no block is split; window "
    "tokens: "
)


def main(argv):
    execute = "--execute" in argv
    with io.open(STATE, "r", encoding="utf-8") as handle:
        state = json.load(handle)
    window = state["log"][WINDOW_START - 1:WINDOW_END]
    tokens = []
    for item in window:
        for token in SF.PAT.findall(item):
            if token not in tokens:
                tokens.append(token)
    summary = LEAD + " ".join(tokens)
    missing = [token for token in tokens if token not in summary]
    if missing:
        raise SystemExit("E_FOLD token coverage missing=%s" % missing)
    size = os.path.getsize(STATE)
    print("FOLD lines=%d window=%d..%d tokens=%d bytes_before=%d"
          % (len(state["log"]), WINDOW_START, WINDOW_END, len(tokens), size))
    if not execute:
        plan, _folded = SF.plan_fold(io.open(STATE, "rb").read(), state,
                                     WINDOW_START, WINDOW_END, summary)
        print("FOLD dry run predicted=%dB margin=%dB"
              % (plan["predicted_bytes"], SF.GATE - plan["predicted_bytes"]))
        print("DRY RUN: pass --execute to fold")
        return 0
    result = SF.fold(REPO, ROUND, FOLD_NO, WINDOW_START, WINDOW_END, summary)
    print("FOLD predicted=%s post_bytes=%d predicted_eq_actual=%s backup=%s"
          % (result.get("predicted_bytes"), result["post_bytes"],
             result["predicted_eq_actual"], result["backup_path"]))
    print("FOLD archive=%s" % json.dumps(result["archive"])[:200])
    if not result["predicted_eq_actual"]:
        raise SystemExit("E_FOLD predicted != actual")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))