# -*- coding: utf-8 -*-
"""R1955 closeout driver part 3: fold carry-note amendment (state
80853B over the 78500B line per the P-2026-09-25-18 law; next
round-start honors it per the R1953/R1898 carry precedent) +
export refresh via check_export_consistency.recompute."""
import datetime as _dt
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")

CARRY = ("\u2014\u2014fold \u627f\u4f20\u6ce8\u8bb0\uff1a\u672c\u8f6e\u6536\u8d26\u540e "
         "state 80853B \u8d8a 78500B \u7ebf 2353B\uff1dP-2026-09-25-18 "
         "\u7b2c\u4e94\u767e\u4e00\u5341\u56db\u5200\u00b7\u4e0b\u8f6e\u8f6e\u9996\u9996\u6d4b"
         "\u88c1\u5b9a\u5151\u73b0\uff08R1953/R1898 \u627f\u4f20\u5148\u4f8b\uff09")

# -- round line: append the fold carry note -------------------------
with io.open(P_STATE, encoding="utf-8", newline="") as fh:
    state = fh.read()
anchor = "queue_tech_open 10\u219210\uff1b\u4e0b\u8f6e FIFO \u961f\u5934=ledger proposal persist\uff3bR1951 \u8865\u79cd\u00b7\u6700\u8001\u5f00\u9879\uff3d\""
assert state.count(anchor) == 1, "round line tail anchor not unique"
state = state.replace(
    anchor,
    "queue_tech_open 10\u219210\uff1b\u4e0b\u8f6e FIFO \u961f\u5934=ledger proposal persist\uff3bR1951 \u8865\u79cd\u00b7\u6700\u8001\u5f00\u9879\uff3d"
    + CARRY + "\"", 1)
parsed = json.loads(state)
assert parsed["tick"] == 1955
assert parsed["log"][-2].endswith("\uff08R1953/R1898 \u627f\u4f20\u5148\u4f8b\uff09")
with io.open(P_STATE, "w", encoding="utf-8", newline="") as fh:
    fh.write(state)
print("state.json: fold carry note appended (%d bytes)"
      % len(state.encode("utf-8")))

# -- export refresh --------------------------------------------------
sys.path.insert(0, os.path.join(ROOT, "src", "os"))
import check_export_consistency as cec  # noqa: E402

derived, state_obj, export_obj, pat = cec.recompute()
assert state_obj["tick"] == 1955, "stale tick: %s" % state_obj["tick"]
export_obj["export_ts"] = _dt.datetime.now().astimezone().isoformat(
    timespec="seconds")
export_obj["ceo_face"]["current"] = (
    "R1955: ledger reports cross-restart persist suite delivered "
    "(7/7; RUNNER 193/193 criteria 1683->1690)")
export_obj["ceo_face"]["latest_artifact"] = (
    "qa/reports-persist-R1955.log + src/sandbox/ledger/"
    "test_reports_persist.py (2026-10-14)")
export_obj["ceo_face"]["next_milestone"] = (
    "next FIFO persist seat (ledger proposal persist suite) by "
    "2026-10-16")
results_row = (
    "R1955: ledger reports cross-restart persist suite 7/7 "
    "(AC-RPP1..RPP7; two-piece restart, immutable three-table "
    "persistence, twelve restart-surviving gates same-code, "
    "continuation recompute, frozen prefix rows, RUNNER 193/193 "
    "criteria 1683->1690; one same-round claim-row erratum honestly "
    "noted); tech consume 1 reseed 1 (refund-recovery persist "
    "seeded; next FIFO head = ledger proposal persist)")
export_obj["results"].insert(0, [ "R1955", results_row])
tick_label = pat["tick_row_label"]
tick_idx = [i for i, r in enumerate(export_obj["results"])
            if len(r) == 2 and r[1] == tick_label]
if tick_idx:
    export_obj["results"][tick_idx[0]][0] = "1955"
else:
    export_obj["results"].append(["1955", tick_label])
if len(export_obj["results"]) > 40:
    export_obj["results"] = export_obj["results"][:40]
if not any(len(r) == 2 and r[1] == tick_label
           for r in export_obj["results"]):
    for _i in range(len(export_obj["results"]) - 1, -1, -1):
        row = export_obj["results"][_i]
        if len(row) == 2 and row[1] != tick_label:
            export_obj["results"].pop(_i)
            break
    export_obj["results"].append(["1955", tick_label])
sd = dict(derived)
sd["method"] = ("machine-derived from state.json log per BD-PROP-001"
                " caliber (check_export_consistency.recompute)")
export_obj["self_drive"] = sd
out = json.dumps(export_obj, indent=1, ensure_ascii=False) + "\n"
with open(P_EXPORT, "wb") as fh:
    fh.write(out.encode("utf-8"))
print("export refreshed: queues=%d/%d/%d tick=%d"
      % (derived["queue_main_open"], derived["queue_tech_open"],
         derived["queue_explore_open"], state_obj["tick"]))
