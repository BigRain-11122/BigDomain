# -*- coding: utf-8 -*-
"""R1959 export repair: the closeout's 40-row trim dropped the tail
tick row (the R1958 fallback block was omitted - same-round honest
fix); this re-runs the export refresh with the full convention."""
import datetime as _dt
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
P_PAYLOAD = os.path.join(HERE, "closeout_payload_R1959.json")

with io.open(P_PAYLOAD, encoding="utf-8") as fh:
    payload = json.load(fh)

sys.path.insert(0, HERE)
import check_export_consistency as cec  # noqa: E402

derived, state_obj, export_obj, pat = cec.recompute()
assert state_obj["tick"] == 1959, "stale tick: %s" % state_obj["tick"]
export_obj["export_ts"] = _dt.datetime.now().astimezone().isoformat(
    timespec="seconds")
export_obj["ceo_face"]["current"] = payload["ceo_current"]
export_obj["ceo_face"]["latest_artifact"] = payload["ceo_artifact"]
export_obj["ceo_face"]["next_milestone"] = payload["ceo_milestone"]
export_obj["results"].insert(0, ["R1959", payload["results_row"]])
tick_label = pat["tick_row_label"]
tick_idx = [i for i, r in enumerate(export_obj["results"])
            if len(r) == 2 and r[1] == tick_label]
if tick_idx:
    export_obj["results"][tick_idx[0]][0] = "1959"
else:
    export_obj["results"].append(["1959", tick_label])
if len(export_obj["results"]) > 40:
    export_obj["results"] = export_obj["results"][:40]
if not any(len(r) == 2 and r[1] == tick_label
           for r in export_obj["results"]):
    for _i in range(len(export_obj["results"]) - 1, -1, -1):
        row = export_obj["results"][_i]
        if len(row) == 2 and row[1] != tick_label:
            export_obj["results"].pop(_i)
            break
    export_obj["results"].append(["1959", tick_label])
sd = dict(derived)
sd["method"] = ("machine-derived from state.json log per BD-PROP-001"
                " caliber (check_export_consistency.recompute)")
export_obj["self_drive"] = sd
out = json.dumps(export_obj, indent=1, ensure_ascii=False) + "\n"
with open(P_EXPORT, "wb") as fh:
    fh.write(out.encode("utf-8"))
print("export repaired: tick row 1959 + R1959 results row +"
      " self_drive recount %s" % json.dumps(sd, sort_keys=True))
