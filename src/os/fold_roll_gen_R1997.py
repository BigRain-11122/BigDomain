# fold_roll_gen_R1997.py - Fold R532 rolling-line generator (gen532
# caliber, mirrors fold_roll_gen_R1992.py): measures the tail-4
# window line byte sizes, extracts the full token catalog
# mechanically (logs_toolkit PAT, zero hand-copying), substitutes
# the mechanical fields into the hand-authored narrative template
# (fold_roll_gen_R1997_head.txt, CJK data file per encoding law),
# and writes the one-line rolling summary to fold_roll_R1997.txt
# for the fold tool. Pure stdlib; ASCII-only source.
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from logs_toolkit import PAT  # noqa: E402

P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_HEAD = os.path.join(HERE, "fold_roll_gen_R1997_head.txt")
OUT = os.path.join(HERE, "fold_roll_R1997.txt")

WINDOW_TAIL = 6
LABELS = [
    "R1994 round line", "R1994 tokens",
    "R1995 round line", "R1995 tokens",
    "R1996 round line", "R1996 tokens",
]
PRE_OP_STATE_BYTES = 76581
WATERLINE = 78500

with io.open(P_STATE, encoding="utf-8") as fh:
    st = json.load(fh)
log = st["log"]
window = log[-WINDOW_TAIL:]
assert len(window) == WINDOW_TAIL, "window short: %d" % len(window)
sizes = [len(ln.encode("utf-8")) for ln in window]
total = sum(sizes)
toks = set()
for ln in window:
    toks |= set(PAT.findall(ln))
catalog = ",".join(sorted(toks))

size_bits = "+".join("%s [%dB]" % (lab, sz)
                     for lab, sz in zip(LABELS, sizes))

with io.open(P_HEAD, encoding="utf-8") as fh:
    template = fh.read().strip()
assert template.count("\n") == 0, "template must be one line"
assert "{" not in template.replace("{SIZE_BITS}", "").replace(
    "{WTOTAL}", "").replace("{NTOK}", "").replace("{CATALOG}", ""), \
    "unexpected placeholder brace in template"

line = (template
        .replace("{SIZE_BITS}", size_bits)
        .replace("{WTOTAL}", str(total))
        .replace("{NTOK}", str(len(toks)))
        .replace("{CATALOG}", catalog))

# zero-loss self-verification against the window (PAT set equality)
roll_toks = set(PAT.findall(line))
missing = toks - roll_toks
assert not missing, "token loss: %s" % sorted(missing)

post_pred = PRE_OP_STATE_BYTES - total + len(line.encode("utf-8"))
with io.open(OUT, "w", encoding="utf-8", newline="") as fh:
    fh.write(line + "\n")

print("PRE_OP %dB WINDOW %dB ROLL %dB" %
      (PRE_OP_STATE_BYTES, total, len(line.encode("utf-8"))))
print("POST_PREDICTED %dB MARGIN_OVER_WATERLINE %dB" %
      (post_pred, WATERLINE - post_pred))
print("TOKENS %d OK (zero-loss self-check passed)" % len(toks))
print("WROTE %s" % OUT)
