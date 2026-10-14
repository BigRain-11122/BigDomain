# -*- coding: utf-8 -*-
"""R1951 claim step: append the pre-registered criteria
AC-TMP1..AC-TMP7 to the tmarket persist row in
state/queue/tech.md BEFORE any suite code exists (honesty law:
criteria registered first). Fail-fast anchors; EOL preserved;
CJK payload read from claim_payload_R1951.json (ASCII law)."""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
P_TECH = os.path.join(os.path.dirname(os.path.dirname(HERE)),
                      "state", "queue", "tech.md")
P_PAYLOAD = os.path.join(HERE, "claim_payload_R1951.json")

with io.open(P_PAYLOAD, encoding="utf-8") as fh:
    payload = json.load(fh)
ROW_HEAD = payload["row_head"]
CLAIM = payload["claim"]

with io.open(P_TECH, encoding="utf-8", newline="") as fh:
    raw = fh.read()
eol = "\r\n" if "\r\n" in raw else "\n"

assert raw.count(ROW_HEAD) == 1, "tmarket row head not unique"
idx = raw.find(ROW_HEAD)
end = raw.find(eol, idx)
assert end > idx, "tmarket row has no line end"

raw = raw[:end] + CLAIM + raw[end:]
with io.open(P_TECH, "w", encoding="utf-8", newline="") as fh:
    fh.write(raw)

with io.open(P_TECH, encoding="utf-8", newline="") as fh:
    chk = fh.read()
assert chk.count(ROW_HEAD) == 1
assert "**AC-TMP1**" in chk and "**AC-TMP7**" in chk
assert "R1951" in chk
print("claim appended: AC-TMP1..TMP7 pre-registered in tech.md "
      "tmarket persist row (before code); eol=%r" % eol)
