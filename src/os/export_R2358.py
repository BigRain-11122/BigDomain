"""export_R2358 - refresh docs/status-export.json from the live state (R2358).

Every count written here is derived in this run: the log line counts come from
src/os/state.json, the proposal counts from docs/proposals.md, and the queue
counts from the queue files themselves. Only the round label and the three
prose summaries are this window's own words.

Dry run by default; --execute writes with a read-back proof.
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
PROPOSALS = os.path.join(ROOT, "docs", "proposals.md")

NOW = datetime.strptime("2026-11-02T02:48:00", "%Y-%m-%dT%H:%M:%S")
STAMP = "2026-11-02T02:48:00+08:00"
DUE = (NOW + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S+08:00")

DO = (
    "R2358 verification window: the carried battery ran first on the committed "
    "R2357 tree and its first run was RED ON DATA, NOT CODE - os-stamp-exempt-"
    "review AC-SER6 named one undeclared closed row, the R2356 product row "
    "whose done bracket had swallowed its whole narrative past the 60-character "
    "stamp payload. The repair was one line at that row's birth site (the "
    "narrative moved outside the bracket, a valid [done 2026-11-01 R2356] left "
    "behind), never a widened criterion and never a new exemption. On the "
    "committed repair tree the retry reads RUNNER PASS 488/488 suites with 3904 "
    "criteria and all four follow-up sections PASS."
)

ARTIFACT = (
    "qa/reconcile-all-R2358-retry.log (798018B, single writer utf-8 LF through "
    "src/os/battery_stream.py) - RUNNER PASS 488/488 suites plus controls 7/7 "
    "in 854.8s with TMP RECLAIM 932/932; the red leg qa/reconcile-all-R2358.log "
    "(797981B) is kept beside it; the matrix regenerated to 488 suites / 3904 "
    "criteria (docs/sandbox-suite-matrix.md, 46718B) and re-read byte-identical."
)

NEXT = (
    "R2359: the product face the register now names - state/queue/tech.md:402 "
    "prefix AC-RWHW1 (review_window_wire), whose six criteria were pinned there "
    "at R2345 BEFORE any code, so the declared-window path finally asks the "
    "declaration history before it hands a window out."
)


def read_json(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def log_counts():
    state = read_json(STATE)
    start = (NOW - timedelta(days=6)).strftime("%Y-%m-%d")
    in_window = [item for item in state["log"] if item[:10] >= start]
    idle = [item for item in in_window if "idle-fast" in item]
    no_pull = [item for item in in_window if "no-pullable" in item]
    return {
        "window_start": start,
        "log_lines_in_window": len(in_window),
        "idle_fast_mention_lines": len(idle),
        "no_pullable_mention_lines": len(no_pull),
        "substantive_non_idle_mention_lines":
            len(in_window) - len(idle) - len(no_pull),
    }


def proposal_counts():
    with io.open(PROPOSALS, "r", encoding="utf-8") as handle:
        text = handle.read()
    heads = [line for line in text.split("\n")
             if line.startswith("### BD-PROP-")]
    opened = [line for line in heads if "状态 open" in line]
    return {"proposals_total": len(heads), "proposals_open": len(opened)}


def queue_counts():
    out = {}
    for name in ("main", "tech", "explore"):
        path = os.path.join(ROOT, "state", "queue", "%s.md" % name)
        with io.open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        out["queue_%s_open" % name] = sum(
            1 for line in text.split("\n") if line.startswith("- [ ]"))
    return out


def main(argv):
    execute = "--execute" in argv
    data = read_json(EXPORT)
    derived, _state, _export, _pat = CEC.recompute()
    counts = {
        "window_start": derived["window"].split("..")[0],
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
        "qa/reconcile-all-R2358-retry.log", "on",
        "R2358 verification: the retry battery on the committed repair tree "
        "reads RUNNER PASS 488/488 suites, criteria 3904, 854.8s; the first "
        "run's red leg stays on disk and the one failure was a queue row whose "
        "done bracket hid its stamp",
    ])
    data["results"].append([
        "R2358",
        "verification window: first run RED on data - os-stamp-exempt-review "
        "AC-SER6 named tech.md:400 as an undeclared closed row because its "
        "done bracket carried a ~500-character narrative past the 60-character "
        "payload; repaired at the birth site in one line (commit 7e503a50) with "
        "no criterion widened and no exemption added; retry PASS 488/488 with "
        "3904 criteria exactly the measured registry after R2357's own suite, "
        "four follow-up sections PASS, battery row closed and product-face-R2359 "
        "opened first=yes at tech line 402 AC-RWHW1; zero product code, 0 points",
    ])
    data["self_drive"] = {
        "window": window,
        "window_days": derived["window_days"],
        "log_lines_in_window": counts["log_lines_in_window"],
        "idle_fast_mention_lines": counts["idle_fast_mention_lines"],
        "no_pullable_mention_lines": counts["no_pullable_mention_lines"],
        "substantive_non_idle_mention_lines":
            counts["substantive_non_idle_mention_lines"],
        "proposals_total": counts["proposals_total"],
        "proposals_open": counts["proposals_open"],
        "queue_main_open": counts["queue_main_open"],
        "queue_tech_open": counts["queue_tech_open"],
        "queue_explore_open": counts["queue_explore_open"],
    }
    tick_rows = [row for row in data["results"]
                 if isinstance(row, list) and len(row) >= 2
                 and row[1] == "OSLoop \u6267\u884c tick"]
    if len(tick_rows) != 1:
        raise SystemExit("E_EXP_TICK rows=%d" % len(tick_rows))
    tick_rows[0][0] = str(_state["tick"])
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    json.loads(text)
    print("EXPORT R2358 self_drive=%s" % json.dumps(data["self_drive"]))
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