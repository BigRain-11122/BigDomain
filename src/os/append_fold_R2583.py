"""R2583 fold disclosure append (short line: the file sits at the gate)."""

import io
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(REPO, "src", "os", "state.json")

LINE = ("2026-11-09 R2583 FOLD: state.json was folded TWICE through the shipped "
        "run face. The first attempt passed window 8..14 as 0-BASED indices "
        "while the predicate indexes 1-BASED, so it folded items 8..13 and "
        "left the R2574 tokens line live - disclosed here rather than hidden; "
        "ledger_lines --check then read DIRTY (ledger_without_round 2574) and "
        "a second fold over the 1-based window 9..9 archived that orphan line, "
        "after which state_fold --check reads FOLD-CLEAR at 77163B against the "
        "78500B gate (margin 1337, 78 log lines) and ledger_lines --check "
        "reads CLEAN. folds 657 and 658, tokens 10 preserved verbatim, archive "
        "VERIFIED.")


def main():
    with io.open(STATE, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    if "R2583 FOLD:" in text:
        raise SystemExit("already present")
    payload = json.loads(text)
    payload["log"].append(LINE)
    text = json.dumps(payload, indent=1, ensure_ascii=False)
    with io.open(STATE, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    print("APPENDED bytes=%d log=%d crlf=%d"
          % (len(text.encode("utf-8")), len(payload["log"]), text.count("\r")))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())