"""gen572_R2043.py - fold R572 rolling-line generator
(R2043 pre-closeout fold, tail-5 window). Reads the narrative
data file (CJK lives in the txt data file per the encoding
law; this source stays pure ASCII), extracts the window tokens
with the single-source PAT imported from logs_toolkit, and
writes the one-line summary file for the fold surgery. The
catalog command then verifies zero token loss before the fold
executes (verify-then-write). Same shape as gen566_R2036.py."""

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normcase(os.path.normpath(
    os.path.join(HERE, "..", "..")))
sys.path.insert(0, HERE)

import logs_toolkit as LT                     # noqa: E402

NARRATIVE = os.path.join(ROOT, "logs",
                         "tmp-gen572-narrative.txt")
SUMMARY = os.path.join(ROOT, "logs",
                       "tmp-gen572-summary.txt")
STATE = os.path.join(ROOT, "src", "os", "state.json")

with io.open(STATE, encoding="utf-8") as fh:
    log = json.loads(fh.read())["log"]
window = log[-5:]
toks = []
seen = set()
for line in window:
    for tok in LT.PAT.findall(line):
        if tok not in seen:
            seen.add(tok)
            toks.append(tok)

with io.open(NARRATIVE, encoding="utf-8") as fh:
    narrative = fh.read().strip()
summary = narrative + "\u2014\u2014catalog: " + "|".join(toks)

with io.open(SUMMARY, "w", encoding="utf-8",
             newline="\n") as fh:
    fh.write(summary + "\n")

print("gen572: window_lines=%d tokens=%d summary_bytes=%d"
      % (len(window), len(toks),
         len(summary.encode("utf-8"))))
