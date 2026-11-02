"""R2407 state fold through the shipped callable, now round-split aware.

The closeout landed the state at 79961B, over the 78500B waterline, so a fold
is due. The window is the SMALLEST prefix that ends on a tokens line, keeps the
target and - new at R2407 - does NOT split a round: the guard added this
window is asked by plan_fold itself, so this script only has to skip a window
whose plan names a round_split instead of trusting the tokens-line heuristic
that produced the R2407 defect in the first place.

Afterwards the moved rounds are re-pinned from ONE live reading through the
shipped residue CLI, because a moved block leaves its rounds undeclared - the
law measured at R2387..R2391 and reused at R2395.

Dry run by default. Stdlib only, ASCII source, no network.
"""

import io
import json
import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_fold as SF  # noqa: E402

TARGET = 73500
GATE = 78500
FOLD_NO = "650"
ROUND = "R2407"
TOKENS_RE = re.compile(r"^R(\d{3,5}) tokens:")


def block_ends(log):
    return [index + 1 for index, line in enumerate(log)
            if TOKENS_RE.match(line)]


def main(argv):
    dry = "--execute" not in argv
    path = SF.state_path(REPO)
    raw, state = SF.read_state(path)
    log = state["log"]
    print("state %d bytes, log %d items, target %d"
          % (len(raw), len(log), TARGET), flush=True)
    chosen = None
    for end in block_ends(log):
        window = log[:end]
        tokens = sorted(set(SF.PAT.findall(" ".join(window))))
        summary = ("Fold %s: %d early log items moved verbatim into the "
                   "monthly archive at a true round-block boundary; tokens "
                   "covered %s." % (ROUND, end, ",".join(tokens)))
        plan, _text = SF.plan_fold(raw, state, 1, end, summary, gate=GATE)
        if plan["tokens_missing"]:
            print("end=%d SKIP token-missing=%d"
                  % (end, len(plan["tokens_missing"])), flush=True)
            continue
        if plan["round_split"]:
            print("end=%d SKIP round-split=%s"
                  % (end, plan["round_split"]), flush=True)
            continue
        print("end=%d predicted=%d gate_ok=%s"
              % (end, plan["predicted_bytes"], plan["gate_ok"]), flush=True)
        if plan["predicted_bytes"] <= TARGET:
            chosen = (end, summary, plan)
            break
    if chosen is None:
        print("REFUSED: no window reaches the target")
        return 2
    end, summary, plan = chosen
    print("chosen window 1..%d predicted %d tokens_total %d"
          % (end, plan["predicted_bytes"], plan["tokens_total"]), flush=True)
    if dry:
        print("DRY: no byte written")
        return 0
    result = SF.fold(REPO, ROUND, FOLD_NO, 1, end, summary, gate=GATE)
    print("fold mode=%s would_fail=%r post_bytes=%r predicted_ok=%r"
          % (result["mode"], result["would_fail"], result.get("post_bytes"),
             result.get("predicted_eq_actual")), flush=True)
    pin = subprocess.run(
        [sys.executable, os.path.join(BASE, "residue_triage_repin.py"),
         "--round", ROUND, "--until", "R2450", "--reason",
         "R2407 fold moved a block; the moved rounds are re-pinned",
         "--execute"],
        cwd=BASE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(pin.stdout.decode("utf-8", "replace").strip()[-300:], flush=True)
    print("REPIN rc=%d" % pin.returncode, flush=True)
    check = SF.check(REPO)
    print("CHECK bytes=%d margin=%d verdict=%s"
          % (check["bytes"], check["margin"], check["verdict"]), flush=True)
    return 0 if (not result["would_fail"]
                 and result.get("predicted_eq_actual")
                 and pin.returncode == 0
                 and check["verdict"] == "FOLD-CLEAR") else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))