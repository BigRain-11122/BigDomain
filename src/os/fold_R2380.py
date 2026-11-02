"""R2380 fold: move the R2371 and R2372 round blocks into the archive.

The closeout would have crossed the 78500B waterline (74258B + this window's
eight items), so the fold runs FIRST at a TRUE round-block boundary: lines
2..18 hold the R2371 block (2..10) and the R2372 block (11..18) with nothing
else. The reservation is this window's own closeout size so the plan proves the
closeout will fit rather than assuming it.

Dry run by default. Stdlib only, ASCII source, no network.
"""

import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_fold as SF  # noqa: E402

STATE = os.path.join(REPO, "src", "os", "state.json")
WINDOW_START = 2
WINDOW_END = 18
FOLD_NO = 644
RESERVE = 6500
PAT = re.compile(r'(?:AC|BD|C|D|O|T|XL|OH|R)-[0-9A-Za-z][0-9A-Za-z]*'
                 r'(?:-[0-9A-Za-z]+)*')


def tokens_of(items):
    seen = []
    for item in items:
        for match in PAT.findall(item):
            if match not in seen:
                seen.append(match)
    return seen


def main(argv):
    execute = "--execute" in argv
    with io.open(STATE, "rb") as handle:
        raw = handle.read()
    state = json.loads(raw.decode("utf-8"))
    log = state["log"]
    window = log[WINDOW_START - 1:WINDOW_END]
    tokens = tokens_of(window)
    summary = ("Fold R2380: log lines %d..%d folded verbatim into the archive "
               "(the R2371 and R2372 round blocks); window tokens: %s"
               % (WINDOW_START, WINDOW_END, " ".join(tokens)))
    plan = SF.fold(REPO, "R2380", FOLD_NO, WINDOW_START, WINDOW_END, summary,
                   reserve=RESERVE, execute=False)
    print("PLAN lines=%d..%d window_lines=%s content=%s tokens=%d missing=%s "
          "predicted=%s margin=%s gate_ok=%s"
          % (plan["window_start"], plan["window_end"], plan["window_lines"],
             plan["window_content_bytes"], plan["tokens_total"],
             plan["tokens_missing"], plan["predicted_bytes"],
             plan["margin"], plan["gate_ok"]))
    if plan["tokens_missing"] or not plan["gate_ok"]:
        print("REFUSED would_fail=%s" % plan["would_fail"])
        return 1
    if not execute:
        print("DRY RUN: pass --execute to fold")
        return 0
    result = SF.fold(REPO, "R2380", FOLD_NO, WINDOW_START, WINDOW_END, summary,
                     reserve=RESERVE, execute=True)
    print("FOLDED predicted=%s measured=%s margin=%s archive=%s"
          % (result["predicted_bytes"], result["new_bytes"],
             result["margin"], result["archive"]))
    with io.open(STATE, "rb") as handle:
        after = len(handle.read())
    print("STATE bytes=%d archive_bytes=%s"
          % (after, result["archive"]["after_bytes"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))