# gen551.py - fold R551 (tail-3 -> one rolling line) + R2021
# state surgery (tick bump + round/tokens append). Byte-surgical:
# raw-text edits only, json.loads validated at the end. New lines
# carry explicit CR endings to keep the CRLF uniform layout (the
# R2020 bare-LF closeout defect repaired at R2021 round start is
# not repeated). CJK content lives in closeout_payload_R2021.json
# (data-file law); this source stays pure ASCII.
import hashlib
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
STATE = os.path.join(ROOT, "src", "os", "state.json")
ARCHIVE = os.path.join(ROOT, "logs", "state-log-archive-2026-10.md")
PREOP = os.path.join(ROOT, "logs", "state-preop-R2021.bak")
PAYLOAD = os.path.join(HERE, "closeout_payload_R2021.json")

pay = json.loads(io.open(PAYLOAD, encoding="utf-8").read())

with io.open(STATE, "r", encoding="utf-8", newline="") as f:
    text = f.read()

gauge = len(text.encode("utf-8"))
preop_sha16 = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

# --- locate the log array tail-3 item lines -------------------
lines = text.split("\n")


def is_log_item(l):
    s = l.strip()
    return s.startswith('"') and (s.endswith('",') or s.endswith('"'))


idx = [i for i, l in enumerate(lines) if is_log_item(l)]
if len(idx) < 3:
    sys.exit("FATAL: cannot locate 3 log tail lines")
t3 = idx[-3:]
tail_lines = [lines[i] for i in t3]
markers = pay["tail_markers"]
for m, l in zip(markers, tail_lines):
    if m not in l:
        sys.exit("FATAL: tail marker mismatch: expected %r in %r"
                 % (m, l[:80]))
indent = tail_lines[0][:len(tail_lines[0]) - len(tail_lines[0].lstrip())]
folded_bytes = sum(len(l.encode("utf-8")) + 1 for l in tail_lines)

# --- preop backup + archive verbatim append --------------------
with io.open(PREOP, "w", encoding="utf-8", newline="") as f:
    f.write(text)
arch_hdr = ("\n# --- R2021 fold append (2026-10-18, 3 lines verbatim:"
            " fold R550 roll line + R2020 round + R2020 tokens"
            " (R2020 = QA charter daily-crawl round: same-day reconcile"
            " battery RUNNER 236/236 + W27 legal-source harvest into"
            " benchmarks/intelligence-wall + smoke pair + group faces;"
            " this R2021 fold archives that spectrum before the"
            " re-retract-persist round appends), fold R551 window,"
            " pre-op sha16 " + preop_sha16 + ")\n")
with io.open(ARCHIVE, "a", encoding="utf-8", newline="") as f:
    f.write(arch_hdr)
    for l in tail_lines:
        f.write(l + "\n")

# --- mechanical token catalog from the 3 folded lines ----------
tok_pat = re.compile(
    r"\b(?:AC|OH|BD|SD|XL|C|D|O|P|R|T|F|U|N|K|Q|MSG|HQ|J)"
    r"-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*")
toks = set()
for l in tail_lines:
    for m in tok_pat.findall(l):
        toks.add(m)
catalog = "|".join(sorted(toks))

# --- build the new lines from the payload ----------------------
rolling = (pay["rolling_line"]
           .replace("{GAUGE}", str(gauge))
           .replace("{FOLDED}", str(folded_bytes))
           .replace("{NTOK}", str(len(toks)))
           .replace("{CATALOG}", catalog))
round_line = pay["round_line"]
tokens_line = pay["tokens_line"]

for s in (rolling, round_line, tokens_line):
    if '"' in s or "\\" in s:
        sys.exit("FATAL: illegal char in new line")

# --- replace tail-3 with rolling + append R2021 pair -----------
# each new line ends with an explicit CR so the join below yields
# uniform CRLF line endings across the whole file
new_items = [indent + '"' + rolling + '",\r',
             indent + '"' + round_line + '",\r',
             indent + '"' + tokens_line + '"\r']
lines[t3[0]:t3[2] + 1] = new_items
text = "\n".join(lines)

# --- top-field updates (byte-surgical) -------------------------
new, n = re.subn(r'"tick": 2020', '"tick": 2021', text, count=1)
if n != 1:
    sys.exit("FATAL: field edit failed: tick")
text = new

# --- validate ---------------------------------------------------
json.loads(text)  # raises on bad json

with io.open(STATE, "w", encoding="utf-8", newline="") as f:
    f.write(text)
final_bytes = len(text.encode("utf-8"))
predicted = (gauge - folded_bytes
             + sum(len(x.encode("utf-8")) + 1 for x in new_items) - 1 + 1)

print("FOLD-OK gauge=%dB folded=%dB tokens=%d preop_sha16=%s"
      % (gauge, folded_bytes, len(toks), preop_sha16))
print("STATE-FINAL=%dB (predicted %dB, delta %d)"
      % (final_bytes, predicted, final_bytes - predicted))
