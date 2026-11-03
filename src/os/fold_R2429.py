"""R2429 waterline fold: move an early, complete round block into the monthly
archive at a TRUE round-block boundary (the shape that cost R2277/R2299/R2354/
R2360/R2407 their batteries), with every PAT token in the window named in the
summary so the coverage law passes.

Dry run first; the plan is printed and nothing is written unless --execute.
"""
import io
import json
import os
import re
import sys

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
SRC = os.path.join(ROOT, "src", "os")
STATE = os.path.join(SRC, "state.json")
sys.path.insert(0, SRC)
import state_fold  # noqa: E402

TOKENS = state_fold.PAT


def round_of(item):
    """The round a log item belongs to: its own leading date+R<n> label."""
    m = re.match(r"\s*(\d{4}-\d{2}-\d{2}) R(\d+)\b", item)
    if m:
        return m.group(2)
    m = re.match(r"\s*R(\d+)\b", item)
    if m:
        return m.group(1)
    m = re.match(r"\s*(?:Fold )?R(\d+)\b", item)
    return m.group(1) if m else None


def choose_window(log):
    """Pick the earliest prefix ending right before a NEW round's first item."""
    n = len(log)
    start = 0
    # skip the leading fold-summary blocks (they carry no round of their own)
    while start < n:
        r = round_of(log[start])
        if r is not None:
            break
        start += 1
    if start >= n:
        raise SystemExit("E_FOLD_NO_ROUND_START")
    first_round = round_of(log[start])
    end = n - 1
    for i in range(n - 1, start, -1):
        r = round_of(log[i])
        prev = round_of(log[i - 1]) if i else None
        if r is not None and r != prev:
            # i is the first item of round r: a true boundary
            end = i - 1
            break
    return start, end, first_round


def main():
    execute = "--execute" in sys.argv
    raw = io.open(STATE, "rb").read()
    state = json.loads(raw.decode("utf-8"))
    log = state["log"]
    start, end, first_round = choose_window(log)
    window = log[start:end + 1]
    tokens = sorted(set(TOKENS.findall("\n".join(window))))
    summary = (
        "Fold R2429: log items %d..%d moved verbatim into the monthly archive "
        "at a true round-block boundary; tokens covered %s."
        % (start, end, ",".join(tokens))
    )
    plan, _ = state_fold.plan_fold(raw, state, start + 1, end + 1, summary)
    print("WINDOW items=%d..%d rounds_start=%s tokens=%d missing=%s round_split=%s "
          "gate_ok=%s predicted_bytes=%d"
          % (start, end, first_round, len(tokens), plan["tokens_missing"],
             plan["round_split"], plan["gate_ok"], plan["predicted_bytes"]))
    if not execute:
        print("DRY RUN - nothing written")
        return
    result = state_fold.fold(ROOT, "R2429", 641, start + 1, end + 1, summary,
                             execute=True)
    print("FOLDED bytes=%d post=%d archive=%s prefix_intact=%s"
          % (result.get("bytes", -1), result.get("post_bytes", -1),
             result.get("archive_path", "?"), result.get("prefix_intact", "?")))


if __name__ == "__main__":
    main()