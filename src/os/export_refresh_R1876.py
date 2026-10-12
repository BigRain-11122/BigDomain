"""R1876 export self_drive refresh after the explore seed restock
(9 -> 10). Recomputes every derived field via the single-source
caliber and rewrites the export; ceo_face and results rows were
written minutes ago by closeout_R1876 and stay untouched."""

import datetime as _dt
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import check_export_consistency as cec  # noqa: E402

P_EXPORT = os.path.join(os.path.dirname(os.path.dirname(BASE)),
                         "docs", "status-export.json")

derived, state_obj, export_obj, pat = cec.recompute()
assert state_obj["tick"] == 1876, "stale tick: %s" % state_obj["tick"]
export_obj["export_ts"] = _dt.datetime.now().astimezone().isoformat(
    timespec="seconds")
sd = dict(derived)
sd["method"] = ("machine-derived from state.json log per BD-PROP-001"
                " caliber (check_export_consistency.recompute)")
export_obj["self_drive"] = sd
out = json.dumps(export_obj, indent=1, ensure_ascii=False) + "\n"
with open(P_EXPORT, "wb") as fh:
    fh.write(out.encode("utf-8"))
print("export refreshed: queues=%d/%d/%d W=%d sub=%d tick=%d"
      % (derived["queue_main_open"], derived["queue_tech_open"],
         derived["queue_explore_open"],
         derived["log_lines_in_window"],
         derived["substantive_non_idle_mention_lines"],
         state_obj["tick"]))
