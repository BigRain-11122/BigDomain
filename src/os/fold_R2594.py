"""Fold the complete R2592 product-round block, tokens carried in the summary.

The fold predicate refuses a window whose AC/D/O/T tokens are not restated in
the summary line, so the token set is EXTRACTED from the very lines being moved
rather than typed. Dry run by default; pass --execute to write.
"""

import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_fold_run as SFR  # noqa: E402

START = 68
END = 75
PAT = re.compile(r'(?:AC|BD|C|D|O|T|XL|OH|R)-[0-9A-Za-z][0-9A-Za-z]*'
                 r'(?:-[0-9A-Za-z]+)*')


def main(argv):
    state = json.loads(io.open(os.path.join(BASE, "state.json"),
                               encoding="utf-8").read())
    window = state["log"][START - 1:END]
    tokens = set()
    for line in window:
        tokens |= set(PAT.findall(line))
    summary = ("2026-11-09 R2594 fold of log items %d..%d (the complete R2592 "
               "product-round block, ending on its push line) moved verbatim "
               "into the monthly archive at a true round-block boundary; "
               "window tokens: %s"
               % (START, END, " ".join(sorted(tokens))))
    args = ["--fold", "--round", "R2594", "--fold-no", "663",
            "--start", str(START), "--end", str(END), "--summary", summary]
    # The shipped CLI has no --execute flag: absence of --dry-run writes.
    if "--execute" not in argv:
        args.append("--dry-run")
    print("summary_bytes=%d tokens=%d"
          % (len(summary.encode("utf-8")), len(tokens)))
    return SFR.main(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))