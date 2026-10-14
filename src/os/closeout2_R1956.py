# -*- coding: utf-8 -*-
"""R1956 closeout part 2: fold carry-note amendment (state 78607B
over the 78500B line per the P-2026-09-25-18 law; next round-start
honors it per the R1955/R1953 carry precedent). Anchor = unique
ASCII-safe head of the round-line tail; insertion lands right
before the closing quote of the round line (bracket-codepoint
agnostic after the a1/a2 probe lesson)."""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
P_STATE = os.path.join(ROOT, "src", "os", "state.json")

CARRY = ("——fold 承传注记：本轮收账后 state 78607B 越 78500B 线"
         " 107B＝P-2026-09-25-18 第五百一十五刀·下轮轮首首测"
         "裁定兑现（R1955/R1953 承传先例）")
ANCHOR = "\u4e0b\u8f6e FIFO \u961f\u5934=ledger clawback persist"

with io.open(P_STATE, encoding="utf-8", newline="") as fh:
    state = fh.read()
assert state.count(ANCHOR) == 1, "round line tail anchor not unique"
idx = state.find(ANCHOR)
qidx = state.find('"', idx)
assert qidx > idx, "no closing quote after anchor"
assert state[qidx - 1] == "\uff3d" or state[qidx - 1] == "\u3015", \
    repr(state[qidx - 3:qidx])
state = state[:qidx] + CARRY + state[qidx:]
parsed = json.loads(state)
assert parsed["tick"] == 1956
assert parsed["log"][-2].endswith("（R1955/R1953 承传先例）")
with io.open(P_STATE, "w", encoding="utf-8", newline="") as fh:
    fh.write(state)
print("state.json: fold carry note appended (%d bytes)"
      % len(state.encode("utf-8")))
