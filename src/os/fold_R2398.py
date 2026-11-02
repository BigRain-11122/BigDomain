"""R2398 state fold at a true round-block boundary, then one residue re-pin.

The closeout left state.json above the 78500B waterline, so the fold runs
through the shipped state_fold callable: the window is the SMALLEST prefix
that ends on a tokens line and lands under the target, and the summary names
every token the moved lines carry (the fold refuses otherwise). Afterwards the
live residue is re-pinned from ONE reading through the shipped re-pin CLI,
because a moved block leaves its rounds undeclared - the law measured at
R2387..R2391.

Stdlib only, ASCII source, no network.
"""

import io
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
ROUND = "R2398"
TOKENS_RE = re.compile(r"^R(\d{3,5}) tokens:")


def block_ends(log):
    return [index + 1 for index, line in enumerate(log)
            if TOKENS_RE.match(line)]


ROUND_RE = re.compile(r"\bR(\d{3,5})\b")


LEAD_RE = re.compile(r"^\s*(?:\d{4}-\d{2}-\d{2}\s+)?(?:Fold\s+)?R(\d{3,5})\b")


def item_round(line):
    """The round an item BELONGS to - its own leading label, not prose."""
    match = LEAD_RE.match(line)
    return None if match is None else match.group(1)


def splits_a_block(lines, end):
    """True when the item after the window belongs to the round it ends on.

    A window that ends on a round's tokens line while that round's own
    remaining items stay live archives the ledger line and leaves the round
    behind - the coverage law then reads it as delivered-without-a-ledger (the
    R2223/R2336/R2398 shape, measured not assumed). Membership is the item's
    OWN leading label, so a later round quoting an older one is not a split.
    """
    match = TOKENS_RE.match(lines[end - 1])
    if match is None:
        return True
    if end >= len(lines):
        return False
    return item_round(lines[end]) == match.group(1)


def main(argv):
    dry = "--execute" not in argv
    path = os.path.join(REPO, "src", "os", "state.json")
    raw, state = SF.read_state(path)
    log = state["log"]
    print("state %d bytes, log %d items, target %d"
          % (len(raw), len(log), TARGET), flush=True)
    chosen = None
    for end in block_ends(log):
        if splits_a_block(log, end):
            print("end=%d SKIP would split a round block" % end, flush=True)
            continue
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
    print("state now %d bytes" % os.path.getsize(path), flush=True)

    command = [sys.executable, os.path.join(BASE, "residue_triage_repin.py"),
               "--execute", "--round", ROUND, "--until", "R2412",
               "--reason", "fold %s moved the live log blocks of the early "
                           "rounds into the monthly archive" % FOLD_NO]
    proc = subprocess.Popen(command, cwd=REPO, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    out, _err = proc.communicate()
    print(out.decode("utf-8", "replace").replace("\r\n", "\n").strip()[-1200:],
          flush=True)
    print("repin rc=%d" % proc.returncode, flush=True)
    check = subprocess.Popen(
        [sys.executable, os.path.join(BASE, "residue_triage.py"), "--check"],
        cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    body, _err = check.communicate()
    text = body.decode("utf-8", "replace").replace("\r\n", "\n").strip()
    print(text.splitlines()[-1] if text else "NO OUTPUT", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))