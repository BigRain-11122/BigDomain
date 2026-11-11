"""R2643 one-off data repair: the fold summary line must use the FOLD dialect.

The fold that moved log items 75..88 (the complete R2639 verification block and
the complete R2641 verification block) wrote its summary as
"R2639 verification block and R2641 verification block fold together ...".
ledger_lines FOLD_SUMMARY_RE only tolerates "^R<n> fold" or "^R<n> folded", so
that line classified as a ROUND NARRATIVE while the R2639 tokens line it owned
had moved into the archive - and the LIVE ledger face then reported round 2639
as having no ledger line (MEASURED: new_missing 2639 after fold 696).

This is a DATA repair of one live log line, not a suite: it follows the
R2522 / R2530 / R2639 one-off repair pattern with a --check face, a dry run that
predicts the exact byte delta, an --execute that hits it, and an idempotent
re-check that writes zero bytes on a second run.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(REPO, "src", "os", "state.json")

OLD_HEAD = ("R2639 verification block and R2641 verification block fold"
            " together")
NEW_LINE = ("R2639 fold of log items 75..88 - the complete R2639 verification"
            " block ending on its push line and the complete R2641"
            " verification block ending on its tokens line; all 5 tokens"
            " preserved verbatim in this line: AC-EDWW1 AC-LGN8 D-CLEAR D-TOP"
            " T-CLEAN")


def main(argv):
    execute = "--execute" in argv
    with io.open(STATE, "r", encoding="utf-8") as handle:
        raw = handle.read()
    state = json.loads(raw)
    hits = [idx for idx, line in enumerate(state.get("log", []))
            if line.startswith(OLD_HEAD)]
    if len(hits) > 1:
        print("E_R2643FS_MULTI hits=%s" % (hits,))
        return 3
    if not hits:
        already = [idx for idx, line in enumerate(state.get("log", []))
                   if line.startswith("R2639 fold of log items 75..88")]
        if already:
            print("ALREADY-REPAIRED line=%d wrote=0" % (already[0] + 1))
            return 0
        print("E_R2643FS_NOT_FOUND")
        return 3
    index = hits[0]
    state["log"][index] = NEW_LINE
    text = json.dumps(state, indent=1, ensure_ascii=False)
    before = len(raw.encode("utf-8"))
    after = len(text.encode("utf-8"))
    print("REPAIR line=%d bytes %d -> %d delta=%+d execute=%s"
          % (index + 1, before, after, after - before, execute))
    if not execute:
        return 0
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    back = io.open(STATE, encoding="utf-8").read()
    ok = NEW_LINE in json.loads(back)["log"] and OLD_HEAD not in back
    print("READBACK ok=%s bytes=%d" % (ok, len(back.encode("utf-8"))))
    return 0 if ok else 5


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
