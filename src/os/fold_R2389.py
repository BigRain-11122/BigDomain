"""fold_R2389 - one waterline fold at a TRUE round-block boundary."""

import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_fold as SF  # noqa: E402


def tokens_of(lines):
    found = []
    for line in lines:
        for match in re.findall(r"R[0-9]{3,4}|[DC]-[0-9]{8}-[0-9]+", line):
            if match not in found:
                found.append(match)
    return found


def main():
    path = SF.state_path(ROOT)
    raw, state = SF.read_state(path)
    log = state["log"]
    chosen = None
    for end in range(2, len(log) + 1):
        if "tokens:" not in log[end - 1]:
            continue
        labels = []
        for line in log[:end]:
            match = re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2} R([0-9]+) ", line)
            if match:
                labels.append(match.group(1))
        summary = ("Fold R2389 window: log lines 1..%d (%d round labels, "
                   "%s..%s) moved verbatim into logs/state-log-archive-2026-"
                   "11.md at a TRUE round-block boundary; window tokens:"
                   % (end, len(labels), labels[0] if labels else "-",
                      labels[-1] if labels else "-"))
        plan = None
        for _attempt in range(4):
            plan, _ = SF.plan_fold(raw, state, 1, end, summary)
            if not plan["tokens_missing"]:
                break
            summary += " " + " ".join(plan["tokens_missing"])
        if plan is None or plan["tokens_missing"] or not plan["gate_ok"]:
            continue
        if plan["predicted_bytes"] > SF.GATE - 3000:
            continue
        chosen = (end, summary, plan)
        break
    if chosen is None:
        sys.stdout.write("REFUSE: no round-block window fits the gate\n")
        return 1
    end, summary, plan = chosen
    sys.stdout.write("PLAN fold_no=647 window=1..%d tokens=%d missing=%d "
                     "summary_bytes=%d predicted=%d margin=%d\n"
                     % (end, plan["tokens_total"],
                        len(plan["tokens_missing"]),
                        len(summary.encode("utf-8")),
                        plan["predicted_bytes"], plan["margin"]))
    result = SF.fold(ROOT, "R2389", 647, 1, end, summary, execute=True)
    sys.stdout.write("FOLD measured=%d predicted=%d margin=%d archive=%s "
                     "backup=%s\n"
                     % (result.get("post_bytes", -1),
                        result.get("predicted_bytes", -1),
                        result.get("margin", -1),
                        result.get("archive", "-"),
                        result.get("backup", "-")))
    return 0


if __name__ == "__main__":
    sys.exit(main())