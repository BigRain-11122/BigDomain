"""fold_R2294.py - one block-aligned waterline fold for R2294.

The closeout pushed state.json past the 78500B gate, so log lines 1..10 (the
three live fold markers plus the whole R2279 and R2280 blocks: narrative,
ledger, self-heal and disclosures) move verbatim into the archive behind one
summary line. The window ends on a block boundary, so no round is split - the
failure mode the R2290 ledger gate caught by name.

The fold number is derived from the real archive headers rather than guessed
(the R2290 lesson: a regex over narrative text once produced a bogus 78496).
The token list is computed from the window itself through state_fold.PAT, so
every token the coverage law checks is present in the summary.
"""

import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import state_fold as SF  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "src", "os", "state.json")
ARCHIVE = os.path.join(ROOT, "logs", "state-log-archive-2026-10.md")

WINDOW_START = 1
WINDOW_END = 10

HEADER_RE = re.compile(r"[Ff]old (\d+)")

# The archive's own numeric markers stop at 597 (the R2282 fold); the rounds
# after it were recorded as unnumbered "Fold R<n>:" lines, and the R2293
# closeout commit records its own fold as 601. The next number is therefore
# 602, stated here rather than derived from a stale marker.
FOLD_NO = 602


def last_fold_number():
    text = io.open(ARCHIVE, "r", encoding="utf-8").read()
    numbers = [int(hit) for hit in HEADER_RE.findall(text)]
    if not numbers:
        return None
    return max(numbers)


def window_tokens():
    state = json.loads(io.open(STATE, "rb").read().decode("utf-8"))
    window = state["log"][WINDOW_START - 1:WINDOW_END]
    tokens = set()
    for line in window:
        tokens |= set(SF.PAT.findall(line))
    return sorted(tokens)


def main(argv):
    execute = "--execute" in argv
    fold_no = FOLD_NO
    seen = last_fold_number()
    tokens = window_tokens()
    summary = (
        "Fold R2294: log lines %d..%d folded verbatim into "
        "logs/state-log-archive-2026-10.md (the three live fold markers plus the "
        "whole R2279 and R2280 blocks: narrative, ledger, self-heal and "
        "disclosures, ending on a block boundary so no round is split); window "
        "tokens: %s" % (WINDOW_START, WINDOW_END, " ".join(tokens)))
    print("FOLD_NO %d (archive max marker %s) TOKENS %d SUMMARY %dB"
          % (fold_no, seen, len(tokens), len(summary.encode("utf-8"))))
    if not execute:
        raw = io.open(STATE, "rb").read()
        state = json.loads(raw.decode("utf-8"))
        plan, _folded = SF.plan_fold(raw, state, WINDOW_START, WINDOW_END, summary)
        print("PLAN window_lines=%d token_ok=%s predicted=%dB margin=%dB "
              "gate_ok=%s" % (plan["window_lines"], plan["token_ok"],
                              plan["predicted_bytes"], plan["margin"],
                              plan["gate_ok"]))
        print("DRY RUN - wrote nothing")
        return 0 if plan["token_ok"] and plan["gate_ok"] else 2
    report = SF.fold(ROOT, "R2294", fold_no, WINDOW_START, WINDOW_END, summary,
                     execute=True)
    for key in sorted(report):
        value = report[key]
        if isinstance(value, list):
            value = "%d items" % len(value)
        print("  %s=%s" % (key, value))
    return 0 if report.get("predicted_eq_actual") else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))