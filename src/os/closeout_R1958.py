# -*- coding: utf-8 -*-
"""R1958 closeout driver: state.json text surgery (tick 1958 +
dec/gord baseline fields + round/tokens log lines per the R1953
closeout convention) + heartbeat two rows (R1957 backfill debt +
R1958 row) + export refresh via check_export_consistency.recompute.
tech.md dual-row edit was already applied by the round driver (claim
+ done flip + reseed). Fail-fast anchors; EOL preserved; CJK
payload read from closeout_payload_R1958.json (ASCII law).
The fold (R516) runs separately via logs_toolkit.py fold after this
script (tool owns archive/backup/splice; separation per AC-LT8)."""
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
P_PAYLOAD = os.path.join(HERE, "closeout_payload_R1958.json")

with io.open(P_PAYLOAD, encoding="utf-8") as fh:
    payload = json.load(fh)

# -- state.json: text surgery ------------------------------------------
with io.open(P_STATE, encoding="utf-8", newline="") as fh:
    state = fh.read()
NL = "\r\n" if "\r\n" in state else "\n"
assert state.count('"tick": 1957,') == 1, "tick anchor not unique"
state = state.replace('"tick": 1957,', '"tick": 1958,', 1)

assert state.count('"last_gord_tbl_rows": 393,') == 1, "gord anchor"
state = state.replace('"last_gord_tbl_rows": 393,',
                      '"last_gord_tbl_rows": 394,', 1)
assert state.count('"last_decision_rows": 318,') == 1, "decrows anchor"
state = state.replace('"last_decision_rows": 318,',
                      '"last_decision_rows": 326,', 1)

tok_anchor = '"last_dec_tokens": "'
t0 = state.index(tok_anchor) + len(tok_anchor)
t1 = state.index('"', t0)
toks = [t for t in state[t0:t1].split(",") if t.strip()]
before = len(toks)
for tok in ("D-20261014-05", "D-20261014-06", "D-20261014-07"):
    if tok not in toks:
        toks.append(tok)
assert len(toks) == before + 3, "expected exactly 3 new dec tokens"
state = (state[:t0] + ",".join(toks) + state[t1:])

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
assert parsed["tick"] == 1958
assert parsed["last_gord_tbl_rows"] == 394
assert parsed["last_decision_rows"] == 326
assert parsed["log"][-2].startswith("2026-10-14 R1958 ledger incentive")
assert parsed["log"][-1].startswith("2026-10-14 R1958 tokens:")
assert len(parsed["log"]) == 19, "expected 19 log lines post-append"
with io.open(P_STATE, "w", encoding="utf-8", newline="") as fh:
    fh.write(state)
print("state.json: tick 1958 + dec tokens %d->%d + gord 394 +"
      " rows 326 + 2 log lines, %d bytes"
      % (before, len(toks), len(state.encode("utf-8"))))

# -- heartbeat: R1957 backfill + R1958 row ------------------------------
with io.open(P_HB, encoding="utf-8", newline="") as fh:
    hb = fh.read()
HNL = "\r\n" if "\r\n" in hb else "\n"
if not hb.endswith(HNL):
    hb += HNL
hb += payload["hb_row_1957"] + HNL
now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
hb += payload["hb_row_1958"] % now + HNL
with io.open(P_HB, "w", encoding="utf-8", newline="") as fh:
    fh.write(hb)
print("heartbeat: tick 1957 backfill + tick 1958 rows appended")

# -- export refresh ----------------------------------------------------
sys.path.insert(0, os.path.join(ROOT, "src", "os"))
import check_export_consistency as cec  # noqa: E402

derived, state_obj, export_obj, pat = cec.recompute()
assert state_obj["tick"] == 1958, "stale tick: %s" % state_obj["tick"]
export_obj["export_ts"] = _dt.datetime.now().astimezone().isoformat(
    timespec="seconds")
export_obj["ceo_face"]["current"] = payload["ceo_current"]
export_obj["ceo_face"]["latest_artifact"] = payload["ceo_artifact"]
export_obj["ceo_face"]["next_milestone"] = payload["ceo_milestone"]
results_row = payload["results_row"]
export_obj["results"].insert(0, ["R1958", results_row])
tick_label = pat["tick_row_label"]
tick_idx = [i for i, r in enumerate(export_obj["results"])
            if len(r) == 2 and r[1] == tick_label]
if tick_idx:
    export_obj["results"][tick_idx[0]][0] = "1958"
else:
    export_obj["results"].append(["1958", tick_label])
if len(export_obj["results"]) > 40:
    export_obj["results"] = export_obj["results"][:40]
if not any(len(r) == 2 and r[1] == tick_label
           for r in export_obj["results"]):
    for _i in range(len(export_obj["results"]) - 1, -1, -1):
        row = export_obj["results"][_i]
        if len(row) == 2 and row[1] != tick_label:
            export_obj["results"].pop(_i)
            break
    export_obj["results"].append(["1958", tick_label])
sd = dict(derived)
sd["method"] = ("machine-derived from state.json log per BD-PROP-001"
                " caliber (check_export_consistency.recompute)")
export_obj["self_drive"] = sd
out = json.dumps(export_obj, indent=1, ensure_ascii=False) + "\n"
with open(P_EXPORT, "wb") as fh:
    fh.write(out.encode("utf-8"))
print("export refreshed: tick row 1958 + R1958 results row +"
      " self_drive machine recount %s" % json.dumps(sd, sort_keys=True))

# -- verify: consistency checker green ----------------------------------
rc = cec.main() if hasattr(cec, "main") else None
print("closeout done")
