import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import state_io  # noqa: E402

STATE = os.path.join(BASE, "state.json")

LINE = (
    "R2779 LEG DECLARATION (R2752 lesson): reconcile-battery-R2779 was launched detached "
    "AFTER the closeout commit 15fc3c8b, pid 77376, with the registry re-measured BY IMPORT on "
    "that committed tree at 676 suites / 5032 criteria / 676 unique names / 676 unique paths. "
    "Two src/os bytes land under the leg by necessity and must be attributed rather than "
    "discovered: src/os/export_R2779.py (the export driver, written before the commit) and "
    "src/os/launch_battery_R2779.py (this launcher, a new src/os byte written when the leg "
    "started). qa/reconcile-all-R2775.log was committed as the record of the adopted red leg. "
    "No preview artifact, no tools/ file and no registry row moves after the launch."
)

doc = json.load(io.open(STATE, encoding="utf-8"))
doc["log"].append(LINE)
state_io.write_document(STATE, doc)
back = json.load(io.open(STATE, encoding="utf-8"))
print("APPENDED log=%d tick=%s ok=%s"
      % (len(back["log"]), back["tick"], back["log"][-1] == LINE))
