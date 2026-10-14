# -*- coding: utf-8 -*-
"""R1959 closeout driver: state.json text surgery (tick 1958 ->
1959; DEC/GORD baselines flat this round) + round/tokens log lines
per the R1953 closeout convention + heartbeat row + export refresh
via check_export_consistency.recompute. tech.md dual-row edit was
already applied by the round driver (done flip + claim criteria +
reseed). Fail-fast anchors; EOL preserved; CJK payload read from
closeout_payload_R1959.json (ASCII law). No fold this round (post
watermark under the 78500B line - next round-start probe owns any
adjudication)."""
import datetime as _dt
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_HB = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
P_PAYLOAD = os.path.join(HERE, "closeout_payload_R1959.json")

with io.open(P_PAYLOAD, encoding="utf-8") as fh:
    payload = json.load(fh)

# -- state.json: text surgery ------------------------------------------
with io.open(P_STATE, encoding="utf-8", newline="") as fh:
    state = fh.read()
NL = "\r\n" if "\r\n" in state else "\n"
assert state.count('"tick": 1958,') == 1, "tick anchor not unique"
state = state.replace('"tick": 1958,', '"tick": 1959,', 1)

close_anchor = NL + "    ]"
cidx = state.rfind(close_anchor)
assert cidx > 0, "log close anchor not found"
prefix = state[:cidx]
assert prefix.rstrip().endswith('"'), "last log item not a string"
new_block = ("," + NL + '                "'
             + payload["round_line"] + '",' + NL
             + '                "'
             + payload["tokens_line"] + '"')
state = prefix + new_block + state[cidx:]
parsed = json.loads(state)
assert parsed["tick"] == 1959
assert parsed["last_gord_tbl_rows"] == 394, "gord flat"
assert parsed["last_decision_rows"] == 326, "dec rows flat"
assert parsed["log"][-2].startswith("2026-10-14 R1959 ledger")
assert parsed["log"][-1].startswith("2026-10-14 R1959 tokens:")
state_bytes = len(state.encode("utf-8"))
# R1958 pattern: post-append watermark over the fold line -> fold
# R517 runs in-window AFTER this closeout (tool owns the surgery:
# archive verbatim + preop backup + splice; separation per AC-LT8).
with io.open(P_STATE, "w", encoding="utf-8", newline="") as fh:
    fh.write(state)
print("state.json: tick 1959 + 2 log lines (DEC/GORD flat), %d bytes"
      " - fold R517 due in-window (over-line by reserve math)"
      % state_bytes)

# -- heartbeat: R1959 row -----------------------------------------------
with io.open(P_HB, encoding="utf-8", newline="") as fh:
    hb = fh.read()
HNL = "\r\n" if "\r\n" in hb else "\n"
if not hb.endswith(HNL):
    hb += HNL
now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
hb += payload["hb_row_1959"] % now + HNL
with io.open(P_HB, "w", encoding="utf-8", newline="") as fh:
    fh.write(hb)
print("heartbeat: tick 1959 row appended")

# -- export refresh ----------------------------------------------------
sys.path.insert(0, os.path.join(ROOT, "src", "os"))
import check_export_consistency as cec  # noqa: E402

derived, state_obj, export_obj, pat = cec.recompute()
assert state_obj["tick"] == 1959, "stale tick: %s" % state_obj["tick"]
export_obj["export_ts"] = _dt.datetime.now().astimezone().isoformat(
    timespec="seconds")
export_obj["ceo_face"]["current"] = payload["ceo_current"]
export_obj["ceo_face"]["latest_artifact"] = payload["ceo_artifact"]
export_obj["ceo_face"]["next_milestone"] = payload["ceo_milestone"]
results_row = payload["results_row"]
export_obj["results"].insert(0, ["R1959", results_row])
tick_label = pat["tick_row_label"]
tick_idx = [i for i, r in enumerate(export_obj["results"])
            if len(r) == 2 and r[1] == tick_label]
if tick_idx:
    export_obj["results"][tick_idx[0]][0] = "1959"
else:
    export_obj["results"].append(["1959", tick_label])
if len(export_obj["results"]) > 40:
    export_obj["results"] = export_obj["results"][:40]
sd = dict(derived)
sd["method"] = ("machine-derived from state.json log per BD-PROP-001"
                " caliber (check_export_consistency.recompute)")
export_obj["self_drive"] = sd
out = json.dumps(export_obj, indent=1, ensure_ascii=False) + "\n"
with open(P_EXPORT, "wb") as fh:
    fh.write(out.encode("utf-8"))
print("export refreshed: tick row 1959 + R1959 results row +"
      " self_drive machine recount %s" % json.dumps(sd, sort_keys=True))

# -- verify: consistency checker green ----------------------------------
rc = cec.main() if hasattr(cec, "main") else None
print("closeout done")
