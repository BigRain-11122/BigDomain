"""fold_R2311.py - one-off waterline fold for the R2311 closeout.

Chooses the smallest WHOLE round-block window whose fold frees enough bytes
for this round's append, builds a summary that covers every window token, and
runs the fold through the shipped state_fold callable (never a hand splice).

  python src/os/fold_R2311.py            dry run (writes nothing)
  python src/os/fold_R2311.py --execute  fold for real
"""

import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import state_fold as SF

ROOT = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(ROOT, "src", "os", "state.json")
ARCHIVE = os.path.join(ROOT, "logs", "state-log-archive-2026-11.md")
GATE = 78500
APPEND_BYTES = 5500
SAFETY = 2500

BLOCK_START = re.compile(r"^(?:20[0-9]{2}-[0-9]{2}-[0-9]{2} R[0-9]{2,}|"
                         r"R[0-9]{2,} tokens:|Fold R[0-9]{2,}:)")


def last_fold_no():
    text = io.open(ARCHIVE, encoding="utf-8", errors="replace").read()
    nums = [int(m) for m in re.findall(r"fold ([0-9]+) window", text)]
    return max(nums) if nums else 0


def main(argv):
    raw = io.open(STATE, "rb").read()
    state = json.loads(raw.decode("utf-8"))
    log = state["log"]
    starts = [i for i, item in enumerate(log) if BLOCK_START.match(item)]
    if not starts or starts[0] != 0:
        print("E_BLOCKS first block does not start at item 0")
        return 3
    ends = [s for s in starts[1:]] + [len(log)]
    fold_no = last_fold_no() + 1
    chosen = None
    for end in ends:
        if end < 2:
            continue
        window = log[:end]
        tokens = sorted(set(SF.PAT.findall("\n".join(window))))
        summary = ("Fold R2311: log lines 1..%d (whole round blocks) moved "
                   "verbatim to the archive; window tokens: %s"
                   % (end, " ".join(tokens)))
        plan, _ = SF.plan_fold(raw, state, 1, end, summary,
                               reserve=APPEND_BYTES)
        need = plan["predicted_bytes"] + APPEND_BYTES + SAFETY
        ok = (not plan["tokens_missing"]) and plan["gate_ok"] and need <= GATE
        print("TRY end=%d predicted=%d need=%d tokens=%d missing=%d ok=%s"
              % (end, plan["predicted_bytes"], need, plan["tokens_total"],
                 len(plan["tokens_missing"]), ok))
        if ok:
            chosen = (end, summary, plan)
            break
    if not chosen:
        print("E_NO_WINDOW no whole-block window frees enough bytes")
        return 3
    end, summary, plan = chosen
    execute = "--execute" in argv
    result = SF.fold(ROOT, "R2311", fold_no, 1, end, summary,
                     reserve=APPEND_BYTES, execute=execute)
    keep = {k: result.get(k) for k in ("window_start", "window_end",
                                       "predicted_bytes", "tokens_total",
                                       "tokens_missing", "would_fail",
                                       "post_bytes", "mode")}
    print("FOLD %s fold_no=%d %s" % (result["mode"], fold_no,
                                     json.dumps(keep)))
    return 3 if result.get("would_fail") else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))