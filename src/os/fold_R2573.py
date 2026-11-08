"""Fold R2573: move the completed round blocks 3..38 into the archive.

Window 3..38 covers R2562 through R2571 (each block ending at its own tokens
line), so the boundary is a true round boundary; the live tail keeps the whole
R2572 block and this window own lines. The summary line carries every token the
shipped predicate extracts from the window.
"""

import io
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(REPO, "src", "os", "state.json")
sys.path.insert(0, BASE)
import state_fold as SF  # noqa

START = 3
END = 38

data = json.load(io.open(STATE, encoding="utf-8"))
window = data["log"][START - 1:END]
tokens = set()
for line in window:
    tokens |= set(SF.PAT.findall(line))
ordered = sorted(tokens)
summary = ("R2573 fold of log lines %d..%d into the archive; all %d tokens "
           "preserved in this line: %s"
           % (START, END, len(ordered), " ".join(ordered)))
print("tokens=%d summary_bytes=%d" % (len(ordered), len(summary.encode("utf-8"))))
cmd = [sys.executable, os.path.join(BASE, "state_fold_run.py"), "--fold",
       "--round", "R2573", "--fold-no", "659",
       "--start", str(START), "--end", str(END), "--summary", summary]
print("RUN", " ".join(cmd[:9]))
returned = subprocess.call(cmd)
print("fold_run rc=%d" % returned)
sys.exit(returned)