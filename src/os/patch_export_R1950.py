# -*- coding: utf-8 -*-
"""Post-fold F3 export re-derivation (R1950): fold R512 changed
the state.json log shape (23 -> 15 lines, rolling line carries
R1944..R1950); docs/status-export.json must re-derive from the
ACTUAL post-fold state (F3 law, BD-PROP-001 caliber). Same
ceo_face payload values as the R1950 closeout (idempotent
re-derivation of self_drive/queues; tick row law per
patch_export_tick_R1946). Pure stdlib."""
import datetime as _dt
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

with open(os.path.join(BASE, "closeout_payload_R1950.json"),
          encoding="utf-8") as fh:
    P = json.load(fh)

import check_export_consistency as cec  # noqa: E402

derived, state_obj, export_obj, pat = cec.recompute()
assert state_obj["tick"] == 1950, "stale tick: %s" % state_obj["tick"]
export_obj["export_ts"] = _dt.datetime.now().astimezone().isoformat(
    timespec="seconds")
export_obj["ceo_face"]["current"] = P["ceo_current"]
export_obj["ceo_face"]["latest_artifact"] = P["ceo_artifact"]
export_obj["ceo_face"]["next_milestone"] = P["ceo_milestone"]
if P["results_row"] not in export_obj["results"]:
    export_obj["results"].insert(0, P["results_row"])
tick_label = pat["tick_row_label"]
tick_idx = [i for i, r in enumerate(export_obj["results"])
            if len(r) == 2 and r[1] == tick_label]
if tick_idx:
    export_obj["results"][tick_idx[0]][0] = str(1950)
else:
    export_obj["results"].append(["1950", tick_label])
if len(export_obj["results"]) > 40:
    export_obj["results"] = export_obj["results"][:40]
# tick-row survival guard (R1946 erratum family law)
if not any(len(r) == 2 and r[1] == tick_label
           for r in export_obj["results"]):
    for _i in range(len(export_obj["results"]) - 1, -1, -1):
        row = export_obj["results"][_i]
        if len(row) == 2 and row[1] != tick_label:
            export_obj["results"].pop(_i)
            break
    export_obj["results"].append(["1950", tick_label])
sd = dict(derived)
sd["method"] = ("machine-derived from state.json log per BD-PROP-001"
                " caliber (check_export_consistency.recompute;"
                " post-fold R512 re-derivation)")
export_obj["self_drive"] = sd
out = json.dumps(export_obj, indent=1, ensure_ascii=False) + "\n"
with open(os.path.join(ROOT, "docs", "status-export.json"), "wb") as fh:
    fh.write(out.encode("utf-8"))
print("export re-derived post-fold R512: queues=%d/%d/%d tick=%d"
      " loglines=%d" % (derived["queue_main_open"],
                        derived["queue_tech_open"],
                        derived["queue_explore_open"],
                        state_obj["tick"], len(state_obj["log"])))
