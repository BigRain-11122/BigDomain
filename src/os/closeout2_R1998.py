# closeout2_R1998.py - remaining closeout steps after the
# state.json + explore.md steps already landed (this takeover
# session flipped the explore claim row by hand with the
# dedicated editor; this driver resumes: heartbeat line, export
# refresh. The state step is NOT re-run (verify only).
# Mirrors closeout2_R1990.py minus the explore step.
import io
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

P_PAYLOAD = os.path.join(HERE, "closeout_payload_R1998.json")
P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_EXPLORE = os.path.join(ROOT, "state", "queue", "explore.md")
P_HEART = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")

PAY = json.loads(io.open(P_PAYLOAD, encoding="utf-8").read())


def die(msg):
    print("ABORT: %s" % msg)
    sys.exit(2)


# ---------- 0. verify state step already landed ----------
st = json.loads(io.open(P_STATE, encoding="utf-8").read())
if st["tick"] != 1998:
    die("state step not landed (tick=%s)" % st["tick"])
if not st["log"][-1].startswith("R1998 tokens"):
    die("state log tail unexpected")
sz = os.path.getsize(P_STATE)
if sz >= 78500:
    die("state over the line: %d" % sz)
print("state.json verified: tick=1998 bytes=%d (already landed)"
      % sz)

# ---------- 0b. verify explore step already landed ----------
raw = io.open(P_EXPLORE, encoding="utf-8", newline="").read()
if raw.count("[done 2026-10-15 R1998]") != 1 and \
        raw.count("\u3014done 2026-10-15 R1998\u3015") != 1:
    die("explore done-note count=%d/%d" % (
        raw.count("[done 2026-10-15 R1998]"),
        raw.count("\u3014done 2026-10-15 R1998\u3015")))
if raw.count("R1998 收账补种") != 1:
    die("explore reseed row count=%d" % raw.count(
        "R1998 收账补种"))
print("explore.md verified: claim flipped done + reseed landed")

# ---------- 1. heartbeat.txt ----------
hb = io.open(P_HEART, encoding="utf-8", newline="").read()
if not hb.endswith("\r\n"):
    hb += "\r\n"
hline = PAY["hb_line"] + "\r\n"
io.open(P_HEART, "w", encoding="utf-8", newline="").write(hb + hline)
print("heartbeat.txt OK: R1998 line appended")

# ---------- 2. docs/status-export.json ----------
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
tick_row = ["1998", label]
rrows = [r for r in results
         if isinstance(r, list) and len(r) >= 2 and r[1] != label]
new_results = [["R1998", PAY["results_row"]]] + rrows[:38] + [
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
print("ALL REMAINING CLOSEOUT EDITS DONE")
