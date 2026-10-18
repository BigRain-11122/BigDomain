# state_append_R2029.py - R2029 state surgery (tick bump +
# round/tokens append). Byte-surgical: raw-text edits only,
# json.loads validated at the end. New lines carry explicit CR
# endings to keep the CRLF uniform layout (gen551 law). CJK
# content lives in closeout_payload_R2029.json (data-file law);
# this source stays pure ASCII.
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
STATE = os.path.join(ROOT, "src", "os", "state.json")
PAYLOAD = os.path.join(HERE, "closeout_payload_R2029.json")

pay = json.loads(io.open(PAYLOAD, encoding="utf-8").read())

with io.open(STATE, "r", encoding="utf-8", newline="") as f:
    text = f.read()

gauge = len(text.encode("utf-8"))

lines = text.split("\n")


def is_log_item(l):
    s = l.strip()
    return s.startswith('"') and (s.endswith('",')
                                 or s.rstrip("\r").endswith('",')
                                 or s.rstrip("\r").endswith('"'))


idx = [i for i, l in enumerate(lines) if is_log_item(l)]
if not idx:
    sys.exit("FATAL: no log item lines found")
i_last = idx[-1]
last_line = lines[i_last]
if pay["last_item_head"] not in last_line:
    sys.exit("FATAL: last item head mismatch: %r"
             % last_line[:80])
indent = last_line[:len(last_line) - len(last_line.lstrip())]

round_line = pay["round_line"]
tokens_line = pay["tokens_line"]
for s in (round_line, tokens_line):
    if '"' in s or "\\" in s:
        sys.exit("FATAL: illegal char in new line")

# last item gains a comma; two new items appended after it
stripped = last_line.rstrip("\r")
assert stripped.endswith('"'), "last item must end with a quote"
lines[i_last] = stripped + ",\r"
new_items = [indent + '"' + round_line + '",\r',
             indent + '"' + tokens_line + '"\r']
lines[i_last + 1:i_last + 1] = new_items
text = "\n".join(lines)

# top-field update (byte-surgical)
new, n = re.subn(r'"tick": 2028', '"tick": 2029', text, count=1)
if n != 1:
    sys.exit("FATAL: field edit failed: tick")
text = new

json.loads(text)  # raises on bad json

with io.open(STATE, "w", encoding="utf-8", newline="") as f:
    f.write(text)
final_bytes = len(text.encode("utf-8"))
st = json.loads(text)
print("APPEND-OK gauge=%dB final=%dB tick=%d log-items=%d"
      % (gauge, final_bytes, st["tick"], len(st["log"])))
assert final_bytes < 78500, "over the line"
assert st["log"][-1].startswith("R2029 tokens:"), "tail check"
print("STATE-APPEND-OK")
