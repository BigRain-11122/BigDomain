# closeout_R1990.py - round closeout driver (pure ASCII; CJK
# payload lives in closeout_payload_R1990.json per data-file law).
# Verify-then-write: every anchor asserted before any byte lands.
# Steps: state.json tick+append (canonical 16-space item indent),
# explore.md claim done-flip + execution note + reseed,
# heartbeat line, export refresh via
# check_export_consistency.recompute.
import io
import json
import os
import re
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

P_PAYLOAD = os.path.join(HERE, "closeout_payload_R1990.json")
P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_EXPLORE = os.path.join(ROOT, "state", "queue", "explore.md")
P_HEART = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")

PAY = json.loads(io.open(P_PAYLOAD, encoding="utf-8").read())
L1 = PAY["l1"]
L2 = PAY["l2"]


def die(msg):
    print("ABORT: %s" % msg)
    sys.exit(2)


# ---------- 1. state.json ----------
raw = io.open(P_STATE, encoding="utf-8", newline="").read()
orig_len = len(raw.encode("utf-8"))
new, n = re.subn(r'"tick":\s*1989\b', '"tick": 1990', raw, count=1)
if n != 1:
    die("tick anchor miss")
raw = new

t = raw.rstrip()
trailing = raw[len(t):]
i = t.rfind("]")
if i < 0 or t[i + 1:].strip() != "}":
    die("state tail structure unexpected: %r" % t[-24:])
head = t[:i].rstrip()
if not head.endswith('"'):
    die("state last log line does not end with quote")
add = (",\r\n                " + json.dumps(L1, ensure_ascii=False)
       + ",\r\n                " + json.dumps(L2, ensure_ascii=False)
       + "\r\n    " + t[i:] + trailing)
predicted = orig_len + len(add.encode("utf-8"))
if predicted >= 78500:
    die("closeout would exceed line: predicted %d" % predicted)
raw2 = head + add
try:
    st = json.loads(raw2)
    assert st["tick"] == 1990
    assert st["log"][-1].startswith("R1990 tokens")
    assert st["log"][-2].startswith("2026-10-15 R1990")
except Exception as e:
    die("post-parse verify: %r" % e)
io.open(P_STATE, "w", encoding="utf-8", newline="").write(raw2)
print("state.json OK: tick=1990 bytes=%d (predicted %d)"
      % (len(raw2.encode("utf-8")), predicted))

# ---------- 2. state/queue/explore.md ----------
raw = io.open(P_EXPLORE, encoding="utf-8", newline="").read()
marker = PAY["explore_marker"]
if raw.count(marker) != 1:
    die("explore claim row count=%d" % raw.count(marker))
line_start = raw.index(marker)
line_end = raw.index("\n", line_start)
line = raw[line_start:line_end]
if not line.startswith("- [ ] "):
    die("claim row already flipped")
if "[done 2026-10-15 R1990]" in line:
    die("claim row already carries done note")
newline = "- [x] " + line[len("- [ ] "):] + PAY["done_note"]
raw2 = (raw[:line_start] + newline + "\n" + PAY["reseed"]
        + raw[line_end:])
io.open(P_EXPLORE, "w", encoding="utf-8", newline="").write(raw2)
print("explore.md OK: claim flipped done + note + reseed")

# ---------- 3. heartbeat.txt ----------
hb = io.open(P_HEART, encoding="utf-8", newline="").read()
if not hb.endswith("\r\n"):
    hb += "\r\n"
hline = PAY["hb_line"] + "\r\n"
io.open(P_HEART, "w", encoding="utf-8", newline="").write(hb + hline)
print("heartbeat.txt OK: R1990 line appended")

# ---------- 4. docs/status-export.json ----------
import check_export_consistency as cec  # noqa: E402

derived, state, _, pat = cec.recompute()
exp = json.loads(io.open(P_EXPORT, encoding="utf-8").read())
exp["export_ts"] = datetime.now().astimezone().isoformat(
    timespec="seconds")
exp["ceo_face"] = {
    "current": PAY["ceo_current"],
    "latest_artifact": PAY["ceo_artifact"],
    "next_milestone": PAY["ceo_next"],
}
results = exp["results"]
label = pat["tick_row_label"]
tick_row = ["1990", label]
rrows = [r for r in results
         if isinstance(r, list) and len(r) >= 2 and r[1] != label]
new_results = [["R1990", PAY["results_row"]]] + rrows[:38] + [
    tick_row]
exp["results"] = new_results
sd = dict(derived)
sd["method"] = ("machine-derived from state.json log per "
                "BD-PROP-001 caliber (check_export_consistency"
                ".recompute)")
exp["self_drive"] = sd
io.open(P_EXPORT, "w", encoding="utf-8", newline="").write(
    json.dumps(exp, ensure_ascii=False, indent=2) + "\n")
print("status-export.json OK: results=%d self_drive window=%s"
      % (len(new_results), sd.get("window")))
print("ALL CLOSEOUT EDITS DONE")
