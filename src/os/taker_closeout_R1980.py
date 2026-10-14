# taker_closeout_R1980.py - 23rd-case crashed-round takeover closeout
# (state byte-surgery tick 1979->1980 + GORD baseline 403->421 + two log
#  lines appended; heartbeat R1979 backfill + R1980 row; status-export
#  refreshed from the verified R1979 payload + taker row + self_drive
#  recompute; CRLF dialects preserved where present)
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
STATE = os.path.join(HERE, "state.json")
PAY = os.path.join(HERE, "closeout_payload_R1980.json")
PAY79 = os.path.join(HERE, "closeout_payload_R1979.json")
HB = os.path.join(ROOT, "heartbeat.txt")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
WATERLINE = 78500

with io.open(PAY, encoding="utf-8") as fh:
    p80 = json.load(fh)
with io.open(PAY79, encoding="utf-8") as fh:
    p79 = json.load(fh)

# ---- 1) state.json byte-surgery --------------------------------------
b = open(STATE, "rb").read()
orig_len = len(b)
assert b.count(b'"tick": 1979') == 1, "tick anchor"
b = b.replace(b'"tick": 1979', b'"tick": 1980')
assert b.count(b'"last_gord_tbl_rows": 403') == 1, "gord anchor"
b = b.replace(b'"last_gord_tbl_rows": 403',
              b'"last_gord_tbl_rows": 421')
tail_anchor = b'"\r\n    ]\r\n}\r\n'
assert b.endswith(tail_anchor), "tail anchor"
round_bytes = p80["round_line"].encode("utf-8")
tokens_bytes = p80["tokens_line"].encode("utf-8")
appendix = (b'",\r\n                "' + round_bytes
            + b'",\r\n                "' + tokens_bytes)
b = b[:-len(tail_anchor)] + appendix + tail_anchor
parsed = json.loads(b.decode("utf-8"))
assert parsed["tick"] == 1980, "post tick"
assert parsed["log"][-1] == p80["tokens_line"], "post tail"
assert parsed["log"][-2].startswith("2026-10-15 R1980"), "post round"
size = len(b)
assert size < WATERLINE, "waterline exceeded: %d" % size
open(STATE, "wb").write(b)
print("STATE-CLOSED tick=1980 size=%d (+%dB) log_lines=%d"
      % (size, size - orig_len, len(parsed["log"])))

# ---- 2) heartbeat backfill + current row ------------------------------
hb_bytes = open(HB, "rb").read()
nl = b"\r\n" if b"\r\n" in hb_bytes[-400:] else b"\n"
if hb_bytes.endswith(nl):
    hb_bytes = hb_bytes[:-len(nl)]
row79 = ("2026-10-15T05:49:00+08:00 | BigDomain OSLoop alive"
         " | tick 1979 | " + p80["hb_r1979"]).encode("utf-8")
import datetime as _dt
now = _dt.datetime.now(_dt.timezone(_dt.timedelta(hours=8)))
ts80 = now.strftime("%Y-%m-%dT%H:%M:%S+08:00")
row80 = (ts80 + " | BigDomain OSLoop alive | tick 1980 | "
         + p80["hb_r1980"]).encode("utf-8")
hb_bytes = hb_bytes + nl + row79 + nl + row80 + nl
open(HB, "wb").write(hb_bytes)
print("HB-APPENDED rows=2 (R1979 backfill + R1980) eol=%s"
      % ("CRLF" if nl == b"\r\n" else "LF"))

# ---- 3) status-export refresh ----------------------------------------
sys.path.insert(0, HERE)
import check_export_consistency as cec

raw = open(EXPORT, "rb").read()
enl = b"\r\n" if b"\r\n" in raw else None
exp = json.loads(raw.decode("utf-8"))
exp["export_ts"] = ts80
exp["ceo_face"]["current"] = p79["current"]
exp["ceo_face"]["latest_artifact"] = p79["latest_artifact"]
exp["ceo_face"]["next_milestone"] = p79["next_milestone"]

results = exp.get("results", [])
tick_label = "OSLoop \u6267\u884c tick"
body = [r for r in results
        if not (isinstance(r, list) and len(r) >= 2
                and r[1] == tick_label)]
body = ([["R1980", p80["results_row_r1980"]],
         ["R1979", p79["results_row"]]] + body)[:39]
exp["results"] = body + [["1980", tick_label]]

derived, _state, _export, _pat = cec.recompute()
exp["self_drive"] = derived

out = json.dumps(exp, indent=1, ensure_ascii=False)
if enl is not None:
    out = out.replace("\n", "\r\n")
open(EXPORT, "wb").write(out.encode("utf-8"))
print("EXPORT-REFRESHED ts=%s results=%d self_drive.window=%s"
      % (ts80, len(exp["results"]), derived["window"]))
