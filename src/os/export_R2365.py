"""export_R2365 - refresh docs/status-export.json from the live state (R2365).

Every count written here is derived in this run through
check_export_consistency.recompute(); only the round label and the three prose
summaries are this window's own words. Dry run by default; --execute writes
with a read-back proof.
"""

import io
import json
import os
import sys
from datetime import datetime, timedelta

import check_export_consistency as CEC

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
STATE = os.path.join(ROOT, "src", "os", "state.json")

NOW = datetime.strptime("2026-11-02T05:53:45", "%Y-%m-%dT%H:%M:%S")
STAMP = "2026-11-02T05:53:45+08:00"
DUE = (NOW + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S+08:00")

DO = (
    "R2365 product window: the floor gauge now asks the occupancy reading - a "
    "row whose module and suite already shipped is discounted from standing "
    "supply and NAMED, so a queue can no longer read FLOOR-MET over a floor of "
    "nothing. Live at the instant the module landed it read tech=8/10-1 while "
    "queue_floor alone still read 9/10."
)

ARTIFACT = (
    "src/os/queue_floor_delivered_wire.py plus its six-criteria suite "
    "(qa/queue-floor-delivered-wire-R2365.log, two identical legs plus three "
    "adjacent suites green) and the live reading it was built for "
    "(qa/queue-floor-delivered-wire-live-R2365.log: main=5/5 tech=8/10-1 "
    "explore=10/10, the discounted row named as line 411 AC-FDW1)."
)

NEXT = (
    "R2366: the product face resuming at state/queue/tech.md:412 prefix "
    "AC-BFH1 (battery_followup_help_wire), whose six criteria were pinned in "
    "that row at R2365 BEFORE any code - battery_followup.py answers a bare "
    "--help with a bad-args exit 5 while the sibling runner answers it as a "
    "question at exit 0."
)


def read_json(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def main(argv):
    execute = "--execute" in argv
    data = read_json(EXPORT)
    derived, _state, _export, _pat = CEC.recompute()
    window = derived["window"]
    data["export_ts"] = STAMP
    data["do"] = DO
    face = data["ceo_face"]
    face["current"] = DO
    face["latest_artifact"] = ARTIFACT
    face["last_artifact"] = ARTIFACT
    face["next_milestone"] = NEXT
    face["next_milestone_due"] = DUE
    face["updated_at"] = STAMP
    data["outs"].append([
        "src/os/queue_floor_delivered_wire.py", "on",
        "R2365 product: the floor gauge discounts a DELIVERED open row from "
        "standing supply and names it, so a queue of shipped rows reads "
        "FLOOR-DEBT instead of a met floor; six criteria green twice and one "
        "live reading that caught the defect it was built for",
    ])
    data["results"].append([
        "R2365",
        "product window: state/queue/tech.md:411 AC-FDW1 "
        "queue_floor_delivered_wire - the floor gauge finally asks the "
        "occupancy reading. The debt gate read CLAIM-FIRST "
        "item=product-face-R2365 and the six criteria were pinned in that row "
        "at R2354 BEFORE any code, all five anchors zero-occupancy at HEAD. "
        "The reading is imported from queue_occupancy (patching its reader "
        "moves the gauge; no module-path scan and no row parser here) and a "
        "DELIVERED open row is discounted from claimable supply while "
        "open/done/gated/claimable stay byte-identical to queue_floor, because "
        "the discount is its own key; an all-delivered queue reads FLOOR-DEBT "
        "with the whole floor as shortfall and the rows named, and a queue "
        "with no prefixed row reads exactly queue_floor's row. SUITE PASS 6/6 "
        "twice identical (qa/queue-floor-delivered-wire-R2365.log, 1552B) "
        "plus three adjacent suites green, wired os-queue-floor-delivered-"
        "wire(6). LIVE: main=5/5 tech=8/10-1 explore=10/10 FLOOR-DEBT "
        "shortfall=2 delivered=1, the discounted row being line 411 AC-FDW1 "
        "itself, while queue_floor alone still read tech=9/10 at that instant. "
        "Row stamped and two REAL measured gaps seeded (AC-BFH1..6, "
        "AC-QFR1..6) so the floor stays 10/10 with no filler. Disclosed: the "
        "live capture first landed utf-16 BOM through a PowerShell redirect "
        "and was transcoded to utf-8 LF (900B to 444B, content identical), "
        "census flags=0 DRIFT-CLEAN; no battery ran, so the next one must read "
        "493 suites / 3934 criteria against R2364's 492/3928",
    ])
    data["self_drive"] = {
        "window": window,
        "window_days": derived["window_days"],
        "log_lines_in_window": derived["log_lines_in_window"],
        "idle_fast_mention_lines": derived["idle_fast_mention_lines"],
        "no_pullable_mention_lines": derived["no_pullable_mention_lines"],
        "substantive_non_idle_mention_lines":
            derived["substantive_non_idle_mention_lines"],
        "proposals_total": derived["proposals_total"],
        "proposals_open": derived["proposals_open"],
        "queue_main_open": derived["queue_main_open"],
        "queue_tech_open": derived["queue_tech_open"],
        "queue_explore_open": derived["queue_explore_open"],
    }
    tick_rows = [row for row in data["results"]
                 if isinstance(row, list) and len(row) >= 2
                 and row[1] == "OSLoop \u6267\u884c tick"]
    if len(tick_rows) != 1:
        raise SystemExit("E_EXP_TICK rows=%d" % len(tick_rows))
    tick_rows[0][0] = str(_state["tick"])
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    json.loads(text)
    print("EXPORT R2365 self_drive=%s" % json.dumps(data["self_drive"]))
    print("EXPORT bytes=%d" % len(text.encode("utf-8")))
    if not execute:
        print("DRY RUN: pass --execute to write")
        return 0
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        back = handle.read()
    ok = back == text and json.loads(back)["export_ts"] == STAMP
    print("READBACK ok=%s" % ok)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))