# -*- coding: utf-8 -*-
"""R1955 closeout driver part 2: state.json text surgery (tick +
round/tokens log lines per the R1953 closeout convention) +
heartbeat row. tech.md dual-row edit already landed in part 1;
this script verifies it idempotently. Fail-fast anchors; EOL
preserved; CJK payload from closeout_payload_R1955.json."""
import datetime as _dt
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
P_TECH = os.path.join(ROOT, "state", "queue", "tech.md")
P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_HB = os.path.join(ROOT, "heartbeat.txt")
P_PAYLOAD = os.path.join(HERE, "closeout_payload_R1955.json")

with io.open(P_PAYLOAD, encoding="utf-8") as fh:
    payload = json.load(fh)

# -- tech.md: verify part-1 landed (idempotent) ----------------------
with io.open(P_TECH, encoding="utf-8", newline="") as fh:
    tech = fh.read()
assert tech.count("- [x] ledger reports") == 1, "reports done row"
assert "**done 2026-10-14 R1955**" in tech, "done note missing"
assert "member refund-recovery" in tech, "reseed row missing"
print("tech.md: reports persist done row + refund-recovery reseed "
      "verified")

# -- state.json: text surgery ----------------------------------------
with io.open(P_STATE, encoding="utf-8", newline="") as fh:
    state = fh.read()
NL = "\r\n" if "\r\n" in state else "\n"
assert state.count('"tick": 1954,') == 1, "tick anchor not unique"
state = state.replace('"tick": 1954,', '"tick": 1955,', 1)
close_anchor = NL + "    ]"
cidx = state.rfind(close_anchor)
assert cidx > 0, "log close anchor not found"
prefix = state[:cidx]
assert prefix.rstrip().endswith('"'), "last log item not a string"
new_block = ("," + NL + '                "'
             + payload["round_line"] + '",' + NL + '                "'
             + payload["tokens_line"] + '"')
state = prefix + new_block + state[cidx:]
parsed = json.loads(state)
assert parsed["tick"] == 1955
assert parsed["log"][-2].startswith("2026-10-14 R1955 ledger reports")
assert parsed["log"][-1].startswith("2026-10-14 R1955 tokens:")
with io.open(P_STATE, "w", encoding="utf-8", newline="") as fh:
    fh.write(state)
print("state.json: tick 1955 + 2 log lines, %d bytes"
      % len(state.encode("utf-8")))

# -- heartbeat --------------------------------------------------------
with io.open(P_HB, encoding="utf-8", newline="") as fh:
    hb = fh.read()
HNL = "\r\n" if "\r\n" in hb else "\n"
now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
hb_row = ("%s | BigDomain OSLoop alive | tick 1955 | reports persist "
          "suite delivered; RUNNER 193/193 criteria 1690; five-silence "
          "green (LEDGER 0, DEC token-flat rows 318, GORD 391 flat, "
          "bench fresh, daily reconcile already in-plate)" % now)
if not hb.endswith(HNL):
    hb += HNL
hb += hb_row + HNL
with io.open(P_HB, "w", encoding="utf-8", newline="") as fh:
    fh.write(hb)
print("heartbeat: tick 1955 row appended")
