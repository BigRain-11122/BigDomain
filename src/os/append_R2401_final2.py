# append_R2401_final2.py - the FINAL measured numbers, appended through the
# same door, superseding the two interim quotes in this window.
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import ledger_line_shape_guard as LLSG  # noqa: E402

STATE = os.path.join(BASE, "state.json")

ITEM = (
    "R2401 final measured numbers, because the door was corrected twice while "
    "this window was open and the earlier quotes are superseded: the date "
    "branch compares with the law own classifier on the text FROM the round "
    "token (a first version sliced after the whole match and so classified "
    "' tokens: ...' as 'other'), and a narrative line that only QUOTES the "
    "token strings is ROUND and passes. Final state of the tree: suite 6/6 "
    "twice with adjacent=3 fails=0 (qa/ledger-line-shape-guard-R2401.log, "
    "1522B, re-captured after the last edit), live capture on the REAL "
    "83393B state with 81 log items and 27 ledger items reading the last real "
    "ledger line R2401 as ACCEPTED local=24000, the dated R2392 candidate as "
    "REFUSED E_LLSG_DATE_PREFIX token=2026-11-02, a dry run predicting 84135 "
    "bytes with wrote=no, a byte-stable --json over the eight pinned keys, "
    "and the module digest 5ee886a51edccd45 unchanged before and after "
    "(qa/ledger-line-shape-guard-live-R2401.log, 516B). Registry 527 suites "
    "/ 4138 criteria is a wiring count read off the SUITES AST; no battery "
    "walked this tree, so reconcile-battery-R2394 stays OPEN with that target."
)


def main():
    verdict = LLSG.append_ledger_line(STATE, ITEM, execute=True)
    if verdict["verdict"] != "ACCEPTED" or verdict["wrote"] != "yes":
        raise SystemExit("E_APPEND: %r" % verdict)
    payload = json.loads(io.open(STATE, "r", encoding="utf-8").read())
    print("STATE log_items=%d bytes=%d"
          % (len(payload["log"]), os.path.getsize(STATE)))
    return 0


if __name__ == "__main__":
    sys.exit(main())