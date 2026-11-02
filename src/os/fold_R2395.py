"""R2395 state fold at a true round-block boundary, then one residue re-pin.

The closeout left state.json above the 78500B waterline, so the fold runs
through the shipped state_fold callable: the window is the SMALLEST prefix
that ends on a tokens line and lands under the target, and the summary names
every token the moved lines carry (the fold refuses otherwise). Afterwards
the moved rounds are re-pinned from ONE live reading through residue_triage,
because a moved block leaves its rounds undeclared - the law measured at
R2387..R2391.

Stdlib only, ASCII source, no network.
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
FOLD_NO = "649"
ROUND = "R2395"
TOKENS_RE = re.compile(r"^R(\d{3,5}) tokens:")


def block_ends(log):
    return [index + 1 for index, line in enumerate(log)
            if TOKENS_RE.match(line)]


def main(argv):
    dry = "--execute" not in argv
    path = os.path.join(REPO, "src", "os", "state.json")
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
    print("fold mode=%s would_fail=%r bytes=%s lines=%s margin=%s"
          % (result.get("mode"), result.get("would_fail"),
             result.get("predicted_bytes"), result.get("window_lines"),
             result.get("margin")), flush=True)
    after = os.path.getsize(path)
    print("state now %d bytes" % after, flush=True)

    rounds = sorted(set(TOKENS_RE.match(line).group(1)
                        for line in log[:end] if TOKENS_RE.match(line)))
    command = [sys.executable, os.path.join(BASE, "residue_triage_repin.py"),
               "--execute", "--declared-by", ROUND, "--until", "R2412"]
    for number in rounds:
        command.extend(["--round", "R%s" % number])
    proc = subprocess.Popen(command, cwd=REPO, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    out, _err = proc.communicate()
    print(out.decode("utf-8", "replace").strip()[-1200:], flush=True)
    print("repin rc=%d rounds=%s" % (proc.returncode, ",".join(rounds)),
          flush=True)
    check = subprocess.Popen(
        [sys.executable, os.path.join(BASE, "residue_triage.py"),
         "--check"], cwd=REPO, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    body, _err = check.communicate()
    text = body.decode("utf-8", "replace").replace("\r\n", "\n").strip()
    print(text.splitlines()[-1] if text else "NO OUTPUT", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))