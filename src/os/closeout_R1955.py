# -*- coding: utf-8 -*-
"""R1955 closeout driver: tech.md dual-row edit (reports persist
done + refund-recovery persist reseed) + state.json tick/round
lines. Fail-fast anchors; EOL preserved; CJK payload read from
closeout_payload_R1955.json (ASCII law)."""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
P_TECH = os.path.join(ROOT, "state", "queue", "tech.md")
P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_PAYLOAD = os.path.join(HERE, "closeout_payload_R1955.json")

with io.open(P_PAYLOAD, encoding="utf-8") as fh:
    payload = json.load(fh)

# -- tech.md: mark done + append done note + append reseed row ------
with io.open(P_TECH, encoding="utf-8", newline="") as fh:
    raw = fh.read()
eol = "\r\n" if "\r\n" in raw else "\n"

head = payload["row_head"]
assert raw.count(head) == 1, "reports persist row head not unique"
idx = raw.find(head)
line_start = raw.rfind("\n", 0, idx) + 1
line_end = raw.find(eol, idx)
assert line_end > idx, "row has no line end"
line = raw[line_start:line_end]
assert line.startswith("- [ ] "), "row not open"
done_line = ("- [x] " + line[len("- [ ] "):]
             + payload["done_note"])
raw = raw[:line_start] + done_line + raw[line_end:]

assert raw.count(payload["reseed_row"][:60]) == 0, \
    "reseed row already present"
raw = raw.rstrip("\r\n") + eol + payload["reseed_row"] + eol

with io.open(P_TECH, "w", encoding="utf-8", newline="") as fh:
    fh.write(raw)

with io.open(P_TECH, encoding="utf-8", newline="") as fh:
    chk = fh.read()
assert chk.count("- [x] ledger reports") == 1
assert "**done 2026-10-14 R1955**" in chk
assert "member refund-recovery" in chk
assert chk.count("- [ ]") >= 9, "open rows dropped below nine"

# -- state.json: tick +1, append round + tokens lines ----------------
with io.open(P_STATE, encoding="utf-8", newline="") as fh:
    st_raw = fh.read()
assert st_raw.endswith("]\n") or st_raw.endswith("]"), \
    "unexpected state tail"
state = json.loads(st_raw)
assert state["tick"] == 1954, "unexpected tick baseline"
state["tick"] = 1955
log = state["log"]
assert isinstance(log, list) and log, "log not a list"
tail = log[-1]
assert "R1954" in tail, "unexpected log tail"
log.append(payload["round_line"])
log.append(payload["tokens_line"])
out = json.dumps(state, ensure_ascii=False, indent=2)
with io.open(P_STATE, "w", encoding="utf-8", newline="") as fh:
    fh.write(out)
with io.open(P_STATE, encoding="utf-8", newline="") as fh:
    chk2 = json.load(fh)
assert chk2["tick"] == 1955
assert len(chk2["log"]) == len(log)
assert "R1955" in chk2["log"][-2]
print("closeout done: tech dual-row + state tick 1955 + 2 log "
      "lines; eol=%r" % eol)
