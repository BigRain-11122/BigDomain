"""fold_R2383: fold 645 at a TRUE round-block boundary, predicted then measured.

Window = log lines 1..11, i.e. the two prior fold summaries plus the whole
R2373 and R2374 round blocks, cutting BEFORE the R2374 line (line 12) so no
block is split (the R2277/R2336 defect). Every token inside the window is
carried in the summary, so token coverage is proved by the fold's own plan.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_fold  # noqa: E402

STATE = os.path.join(REPO, "src", "os", "state.json")
WINDOW_START = 1
WINDOW_END = 11
FOLD_NO = "645"


def main(argv):
    execute = "--execute" in argv
    with io.open(STATE, "r", encoding="utf-8") as handle:
        log = json.load(handle)["log"]
    window = log[WINDOW_START - 1:WINDOW_END]
    # The token law is the fold module's OWN pattern, not a second one.
    tokens = sorted({tok for line in window
                     for tok in state_fold.PAT.findall(line)})
    summary = ("Fold R2383: log lines %d..%d folded verbatim into the archive "
               "(the two prior fold summaries and the whole R2373 and R2374 "
               "round blocks), cut BEFORE the R2374 narrative line at a TRUE "
               "round-block boundary so no block is split; window tokens: %s"
               % (WINDOW_START, WINDOW_END, " ".join(tokens)))
    result = state_fold.fold(REPO, "R2383", FOLD_NO, WINDOW_START, WINDOW_END,
                             summary, execute=execute)
    print("FOLD mode=%s window=%d..%d tokens=%d missing=%r gate_ok=%s"
          % (result.get("mode"), WINDOW_START, WINDOW_END, len(tokens),
             result.get("tokens_missing"), result.get("gate_ok")))
    for key in ("predicted_bytes", "post_bytes", "predicted_eq_actual",
                "preop_sha16", "archive", "backup_path"):
        print("  %s=%r" % (key, result.get(key)))
    if execute and result.get("would_fail"):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))