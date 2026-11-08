"""R2567 disclosure append: the archive must not be the only copy.

logs/ is gitignored, so the 192 log lines this window moved out of state.json
would exist only on this disk. The archive file is therefore force-added to git
and this line records why.
"""
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")

LINE = (
    "R2567 disclosure added before commit: logs/ is gitignored, so the 192 "
    "log lines this fold moved out of state.json would have existed only on "
    "this disk. logs/state-log-archive-2026-11.md (257082B, the append-only "
    "verbatim block) and logs/state-preop-R2567.bak (327622B, the exact "
    "pre-fold bytes) are therefore FORCE-ADDED to git this window, and the "
    "law that the archive is the only copy of folded history is named as a "
    "real continuity defect for the next window to fix at its birth site "
    "(a shipped fold should refuse to run when its archive is not trackable)."
)


def main():
    raw = open(STATE, "rb").read()
    text = raw.decode("utf-8")
    data = json.loads(text)
    if json.dumps(data, indent=1, ensure_ascii=False) != text:
        print("REFUSED E_SA_RT_LAYOUT")
        return 3
    data["log"].append(LINE)
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(data, indent=1, ensure_ascii=False))
    size = os.path.getsize(STATE)
    print("STATE log=%d after=%dB gate=78500 ok=%s"
          % (len(data["log"]), size, size <= 78500))
    return 0 if size <= 78500 else 2


if __name__ == "__main__":
    sys.exit(main())