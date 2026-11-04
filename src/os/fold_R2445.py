"""fold_R2445 - plan and (optionally) execute one waterline fold.

The window always starts at item 1 and ends at a round's own tokens line, so
every moved block is whole. The summary carries every token the moved window
mentions, which the shipped plan_fold requires. Dry run by default.
"""

import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_fold  # noqa: E402

TOKENS_RE = re.compile(r"^R(\d{3,5}) tokens:")
PAT = state_fold.PAT


def main(execute):
    path = state_fold.state_path(ROOT)
    raw, state = state_fold.read_state(path)
    log = state["log"]
    ends = [i + 1 for i, line in enumerate(log) if TOKENS_RE.match(line)]
    plans = []
    for end in ends:
        window = log[:end]
        tokens = set()
        for line in window:
            tokens |= set(PAT.findall(line))
        summary = ("Fold R2445: log items 1..%d moved verbatim into the "
                   "monthly archive at a true round-block boundary; tokens "
                   "covered %s" % (end, ",".join(sorted(tokens))))
        try:
            plan, _ = state_fold.plan_fold(raw, state, 1, end, summary,
                                           reserve=6000)
        except state_fold.StateFoldError as exc:
            print("E %s %s" % (end, exc.code))
            continue
        clean = (not plan["round_split"] and plan["token_ok"]
                 and plan["gate_ok"])
        plans.append((end, clean, plan, summary))
        print("END %3d clean=%s lines=%3d predicted=%d margin=%d split=%s "
              "tokens=%d missing=%d"
              % (end, clean, plan["window_lines"], plan["predicted_bytes"],
                 plan["margin"], plan["round_split"], plan["tokens_total"],
                 len(plan["tokens_missing"])))
    good = [row for row in plans if row[1]]
    if not good:
        print("NO CLEAN PLAN")
        return 2
    end, clean, plan, summary = good[0]
    print("CHOSEN end=%d predicted=%d margin=%d" % (end,
                                                    plan["predicted_bytes"],
                                                    plan["margin"]))
    if not execute:
        return 0
    result = state_fold.fold(ROOT, "R2445", 2445, 1, end, summary,
                             reserve=6000, execute=True)
    for key in ("mode", "round", "fold_no", "window_start", "window_end",
                "window_lines", "predicted_bytes", "margin", "preop_sha16",
                "newline", "folded_log_len", "would_fail"):
        print("  %s=%s" % (key, result.get(key)))
    return 0 if not result.get("would_fail") else 2


if __name__ == "__main__":
    sys.exit(main("--execute" in sys.argv[1:]))