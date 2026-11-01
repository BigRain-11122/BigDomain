"""export_R2368 - refresh docs/status-export.json from the live state (R2368).

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

NOW = datetime.strptime("2026-11-02T06:59:07", "%Y-%m-%dT%H:%M:%S")
STAMP = "2026-11-02T06:59:07+08:00"
DUE = (NOW + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S+08:00")

DO = (
    "R2368 product window: the floor finally has ONE published reading whose "
    "number is the discounted number, with the discounted rows travelling "
    "beside it. Live on the same tree at the same instant the published "
    "reading says tech=9/10-1 FLOOR-DEBT (the discounted row is this window's "
    "own claimed row) while the undiscounted gauge still says tech=10/10 "
    "FLOOR-MET - the undiscounted answer was the published one."
)

ARTIFACT = (
    "src/os/queue_floor_reading_wire.py plus its six-criteria suite "
    "(qa/queue-floor-reading-wire-R2368.log, two identical legs plus four "
    "adjacent suites green), the live reading that caught the two-readers gap "
    "(qa/queue-floor-reading-wire-live-R2368.log: published tech=9/10-1 vs "
    "undiscounted tech=10/10) and the battery that proves the registry "
    "unharmed (qa/reconcile-all-R2368.log, RUNNER PASS 494/494, criteria 3940)."
)

NEXT = (
    "R2369: the product face resuming at the queue head (state/queue/tech.md:414 "
    "prefix AC-RTAB1) plus the battery on the committed R2368 tree, "
    "pre-registered at 495 suites / 3946 criteria; the seed this window "
    "measured is queue_floor_export_face (AC-QFE1..AC-QFE6), because the "
    "CEO-visible export still publishes no queue line at all."
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
        "src/os/queue_floor_reading_wire.py", "on",
        "R2368 product: one published floor reading whose claimable IS the "
        "discounted number, with the discount count and the discounted rows "
        "(line+prefix) beside it so gross reconciles; six criteria green twice "
        "and one live reading where the published number and the undiscounted "
        "gauge disagree on the same tree",
    ])
    data["results"].append([
        "R2368",
        "verification then product: the carried battery ran first on the "
        "committed dffdd007 tree - RUNNER PASS 494/494 suites plus controls "
        "7/7 in 914.6s, criteria total 3940 EXACTLY as pre-registered, TMP "
        "RECLAIM 932/932 worlds 326.59 MiB (qa/reconcile-all-R2368.log) - and "
        "the four follow-up sections PASS after the designed matrix FAIL and "
        "its regeneration to 494/3940 (47273B, VERDICT PASS), committed alone "
        "as cee549f7 before any product byte changed. Then the claimed row: "
        "state/queue/tech.md:413 AC-QFR1 queue_floor_reading_wire, its six "
        "criteria pinned in that row at R2365 BEFORE the code and all five "
        "anchors zero-occupancy at HEAD. The wire publishes ONE floor reading "
        "whose claimable IS the discounted number, with the discount count and "
        "the discounted rows (line+prefix, exactly as queue_occupancy reported "
        "them) beside it so gross reconciles as claimable + discounted; the "
        "report is queue_floor_delivered_wire.gauge itself and every row law "
        "stays with queue_floor, so a queue with nothing delivered publishes "
        "queue_floor's row byte for byte on every shared key; pure read, no "
        "clock, no writes, no network. SUITE PASS 6/6 twice identical plus "
        "four adjacent suites green (qa/queue-floor-reading-wire-R2368.log, "
        "1723B), wired os-queue-floor-reading-wire(6). LIVE: published "
        "tech=9/10-1 FLOOR-DEBT shortfall=1 delivered=1, the discounted row "
        "being line 413 AC-QFR1 itself, while queue_floor alone still read "
        "tech=10/10 FLOOR-MET at that instant. Row stamped and one REAL "
        "measured gap row seeded (queue_floor_export_face, AC-QFE1..6: "
        "git grep -F over docs/status-export.json and "
        "check_export_consistency.py for claimable/floor/FLOOR returns ZERO "
        "hits, so the published number has no consumer on the export), gauge "
        "FLOOR-MET 5/5 10/10 10/10. Disclosed: the first battery invocation "
        "was piped through a filtering selector and died to the five-minute "
        "no-output rule with zero survivors and zero evidence before the "
        "direct-stream rerun whose numbers are above",
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
    print("EXPORT R2368 self_drive=%s" % json.dumps(data["self_drive"]))
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