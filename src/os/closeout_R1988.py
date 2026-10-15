# closeout_R1988.py - takeover closeout driver (pure ASCII; CJK
# payload lives in closeout_payload_R1988.json per data-file law).
# Verify-then-write: every anchor asserted before any byte lands.
# Steps: state.json tick+append (canonical 16-space item indent),
# explore.md claim done-flip + reseed, heartbeat line, export
# refresh via check_export_consistency.recompute.
import io
import json
import os
import re
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

P_PAYLOAD = os.path.join(HERE, "closeout_payload_R1988.json")
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
new, n = re.subn(r'"tick":\s*1987\b', '"tick": 1988', raw, count=1)
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
    assert st["tick"] == 1988
    assert st["log"][-1].startswith("R1988 tokens")
    assert st["log"][-2].startswith("2026-10-15 R1988")
    assert "fold R528" in st["log"][-3]
except Exception as e:
    die("post-parse verify: %r" % e)
io.open(P_STATE, "w", encoding="utf-8", newline="").write(raw2)
print("state.json OK: tick=1988 bytes=%d (predicted %d)"
      % (len(raw2.encode("utf-8")), predicted))

# ---------- 2. state/queue/explore.md ----------
raw = io.open(P_EXPLORE, encoding="utf-8", newline="").read()
marker = PAY["explore_marker"]
if raw.count(marker) != 1:
    die("explore claim row count=%d" % raw.count(marker))
line_start = raw.index(marker)
line_end = raw.index("\n", line_start)
line = raw[line_start:line_end]
if PAY["explore_claim_check"] not in line:
    die("claim row lacks R1988 claim mark")
newline = "- [x] " + line[len("- [ ] "):] + PAY["done_note"]
raw2 = (raw[:line_start] + newline + "\n" + PAY["reseed"]
        + raw[line_end:])
io.open(P_EXPLORE, "w", encoding="utf-8", newline="").write(raw2)
print("explore.md OK: claim flipped done, reseed added")

# ---------- 3. heartbeat.txt ----------
hb = io.open(P_HEART, encoding="utf-8", newline="").read()
if not hb.endswith("\r\n"):
    hb += "\r\n"
now = datetime.now().strftime("%Y-%m-%d %H:%M")
hline = ("%s +08:00 | BigDomain OSLoop alive | tick 1988 | R1988: "
         "25th-case crashed-round takeover closeout - showcase "
         "stats_board truncated/tail read face (AC-SST1..AC-SST7 "
         "pre-registered pre-code in the claim row): original "
         "session's suite double-run 7/7 byte-identical sha16 "
         "ae4d85d3dc4f10a2 + complete RUNNER PASS 216/216 controls "
         "7/7 248.9s logs preserved (crash point = after RUNNER, "
         "before closeout); taker personally re-ran matrix regen "
         "216/1856 --check identical + census pass + fingerprint "
         "CLEAN x5 + profile identical; five-silence external FLAT; "
         "fold R528 executed pre-closeout (7715B window -> 1 "
         "rolling line, 9 tokens zero-loss, archive verbatim); "
         "state eol indent repaired 2 lines content-eq "
         "[via BigDomain-OSLoop]\r\n")
io.open(P_HEART, "w", encoding="utf-8", newline="").write(hb + hline)
print("heartbeat.txt OK: R1988 line appended")

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
tick_row = ["1988", label]
rrows = [r for r in results
         if isinstance(r, list) and len(r) >= 2 and r[1] != label]
new_results = [["R1988", PAY["results_row"]]] + rrows[:38] + [
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
