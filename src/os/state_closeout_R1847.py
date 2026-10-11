"""Byte surgery for src/os/state.json: bump tick and append R1847 log lines.

Preserves PS layout byte-exactly (CRLF + 16-space item lines, no BOM).
Payload (Chinese text) is loaded from state_payload_R1847.json (data file,
encoding law). No json.dump full-file rewrite (R1710 discipline).
"""

import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "state.json")
PAYLOAD = os.path.join(BASE, "state_payload_R1847.json")

with open(PAYLOAD, encoding="utf-8") as f:
    payload = json.load(f)
lines_new = payload["lines"]
assert len(lines_new) == 2, "expected exactly 2 new log lines"

raw = open(STATE, "rb").read()
assert raw[:3] != b"\xef\xbb\xbf", "unexpected BOM"
text = raw.decode("utf-8")
assert "\r\n" in text
assert text.count("\n") == text.count("\r\n"), "bare LF present"
lines = text.split("\r\n")

tick_idx = None
for i, l in enumerate(lines):
    if '"tick": 1846,' in l:
        tick_idx = i
        break
assert tick_idx is not None, "tick line not found"
lines[tick_idx] = lines[tick_idx].replace('"tick": 1846,', '"tick": 1847,')

close_idx = None
for i, l in enumerate(lines):
    if i > tick_idx and l.strip() == "]":
        close_idx = i
        break
assert close_idx is not None, "log array close not found"
last_item = lines[close_idx - 1]
assert last_item.startswith(" " * 16), "log item indent drift"
stripped = last_item.rstrip()
assert stripped.endswith('"') and not stripped.endswith(","), "last item layout drift"

lines[close_idx - 1] = stripped + ","
item_a = " " * 16 + json.dumps(lines_new[0], ensure_ascii=False)
item_b = " " * 16 + json.dumps(lines_new[1], ensure_ascii=False)
assert "\r" not in item_a and "\n" not in item_a and "\r" not in item_b and "\n" not in item_b
lines[close_idx:close_idx] = [item_a + ",", item_b]

out_text = "\r\n".join(lines)
obj = json.loads(out_text)  # semantic sanity before write
assert obj["tick"] == 1847
assert len(obj["log"]) == 20, "expected 20 log items after append"
assert obj["log"][-2].startswith("2026-10-12 R1847") and obj["log"][-1].startswith("2026-10-12 R1847")

open(STATE, "wb").write(out_text.encode("utf-8"))
print("surgery ok bytes=%d log_items=%d" % (len(out_text.encode("utf-8")), len(obj["log"])))
