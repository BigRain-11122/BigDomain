# state_closeout_R1979.py - byte-surgical state.json closeout
# (tick, GORD baseline, aux decision rows, two log lines appended;
#  CRLF dialect preserved; size verified under the 78500B waterline)
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, "state.json")
PAYLOAD = os.path.join(HERE, "closeout_payload_R1979.json")
WATERLINE = 78500

with io.open(PAYLOAD, encoding="utf-8") as fh:
    payload = json.load(fh)

b = open(P, "rb").read()
orig = b

# 1) tick
assert b.count(b'"tick": 1978') == 1, "tick anchor"
b = b.replace(b'"tick": 1978', b'"tick": 1979')

# 2) GORD baseline (pipe-rows caliber, group-side compaction -12)
assert b.count(b'"last_gord_tbl_rows": 415') == 1, "gord anchor"
b = b.replace(b'"last_gord_tbl_rows": 415',
              b'"last_gord_tbl_rows": 403')

# 3) auxiliary decision rows baseline (nonblank rows, UTF-8 caliber)
assert b.count(b'"last_decision_rows": 329') == 1, "dec-rows anchor"
b = b.replace(b'"last_decision_rows": 329',
              b'"last_decision_rows": 266')

# 4) append round line + tokens line before the log array close
tail_anchor = b'"\r\n    ]\r\n}\r\n'
assert b.endswith(tail_anchor), "tail anchor"
round_bytes = payload["round_line"].encode("utf-8")
tokens_bytes = payload["tokens_line"].encode("utf-8")
appendix = (b'",\r\n                "' + round_bytes
            + b'",\r\n                "' + tokens_bytes)
b = b[:-len(tail_anchor)] + appendix + tail_anchor

# 5) verify: json-parsable, tick correct, size under waterline
parsed = json.loads(b.decode("utf-8"))
assert parsed["tick"] == 1979, "post tick"
assert parsed["log"][-1] == payload["tokens_line"], "post tail"
assert parsed["log"][-2].startswith("2026-10-15 R1979"), "post round"
size = len(b)
assert size < WATERLINE, "waterline exceeded: %d" % size
open(P, "wb").write(b)
print("STATE-CLOSED tick=1979 size=%d (+%dB) log_lines=%d"
      % (size, size - len(orig), len(parsed["log"])))
