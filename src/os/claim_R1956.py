# -*- coding: utf-8 -*-
"""R1956 claim step: append the pre-registered criteria
AC-PLP1..AC-PLP7 to the ledger proposal persist row in
state/queue/tech.md BEFORE any suite code exists (honesty law:
criteria registered first). Fail-fast anchors; EOL preserved;
CJK payload read from claim_payload_R1956.json (ASCII law).
Row located via the ASCII prefix (zero CJK hand-copy)."""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
P_TECH = os.path.join(os.path.dirname(os.path.dirname(HERE)),
                      "state", "queue", "tech.md")
P_PAYLOAD = os.path.join(HERE, "claim_payload_R1956.json")

with io.open(P_PAYLOAD, encoding="utf-8") as fh:
    payload = json.load(fh)
ROW_PREFIX = payload["row_head"]
CLAIM = payload["claim"]

with io.open(P_TECH, encoding="utf-8", newline="") as fh:
    raw = fh.read()
eol = "\r\n" if "\r\n" in raw else "\n"

lines = raw.split(eol)
hits = [i for i, ln in enumerate(lines)
        if ln.startswith(ROW_PREFIX)]
assert len(hits) == 1, "proposal persist row not unique: %d" % len(hits)
idx = hits[0]
assert lines[idx].startswith("- [ ] "), "row not open"

lines[idx] = lines[idx] + CLAIM
raw = eol.join(lines)
with io.open(P_TECH, "w", encoding="utf-8", newline="") as fh:
    fh.write(raw)

with io.open(P_TECH, encoding="utf-8", newline="") as fh:
    chk = fh.read()
chk_lines = chk.split(eol)
assert sum(1 for ln in chk_lines
           if ln.startswith(ROW_PREFIX)) == 1
assert "**AC-PLP1**" in chk and "**AC-PLP7**" in chk
assert "R1956" in chk
print("claim appended: AC-PLP1..PLP7 pre-registered in tech.md "
      "proposal persist row (before code); eol=%r" % eol)
