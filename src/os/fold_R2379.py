"""Plan and execute the R2379 waterline fold.

Finds the smallest window that starts at log line 1, ends on a tokens
ledger line AND on a round-block boundary, covers every token it moves and
lands under the gate with the reserve kept. Pure stdlib, ASCII, no clock.
"""

import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE, "src", "os"))

import state_fold

STATE = os.path.join(BASE, "src", "os", "state.json")
RESERVE = 6000
FOLD_NO = 644
ROUND_LABEL = "R2379"
ROUND_START = re.compile(r"^\d{4}-\d\d-\d\d R\d+")


def is_block_end(log, end):
    """True when log[end - 1] is the LAST item of its round block."""
    if end >= len(log):
        return True
    return bool(ROUND_START.match(log[end]))


def tokens_of(window):
    found = set()
    for line in window:
        found |= set(state_fold.PAT.findall(line))
    return found


def main(argv):
    execute = "--execute" in argv
    raw, state = state_fold.read_state(STATE)
    log = state["log"]
    count = len(log)
    print("state bytes=%d log_lines=%d" % (len(raw), count))
    chosen = None
    for end in range(1, count + 1):
        line = log[end - 1]
        if not (line.startswith("R") and " tokens:" in line[:24]):
            continue
        if not is_block_end(log, end):
            print("-- end=%d NOT-A-BLOCK-BOUNDARY" % end)
            continue
        window = log[:end]
        toks = sorted(tokens_of(window))
        summary = ("Fold %s: log lines 1..%d folded verbatim into the "
                   "archive so the closeout fits the waterline; window ends "
                   "on a tokens ledger line AND on a round-block boundary; "
                   "window tokens: %s"
                   % (ROUND_LABEL, end, " ".join(toks)))
        plan, _text = state_fold.plan_fold(raw, state, 1, end, summary,
                                           reserve=RESERVE)
        mark = "OK " if plan["gate_ok"] and plan["token_ok"] else "-- "
        print("%send=%d lines=%d tokens=%d predicted=%d margin=%d missing=%d"
              % (mark, end, plan["window_lines"], plan["tokens_total"],
                 plan["predicted_bytes"], plan["margin"],
                 len(plan["tokens_missing"])))
        if plan["gate_ok"] and plan["token_ok"] and chosen is None:
            chosen = (end, summary, plan)
    if chosen is None:
        print("E_R2379_NO_FOLDABLE_WINDOW")
        return 3
    end, summary, plan = chosen
    print("CHOSEN end=%d predicted=%d margin=%d"
          % (end, plan["predicted_bytes"], plan["margin"]))
    if not execute:
        print("DRY RUN - nothing written")
        return 0
    result = state_fold.fold(BASE, ROUND_LABEL, FOLD_NO, 1, end, summary,
                             reserve=RESERVE, execute=True)
    print(json.dumps(result, indent=2, sort_keys=True))
    fresh = os.path.getsize(STATE)
    print("POST bytes=%d %s" % (fresh, json.dumps(state_fold.measure(fresh),
                                                  sort_keys=True)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))