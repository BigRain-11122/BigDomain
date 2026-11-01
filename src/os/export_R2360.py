"""export_R2360 - refresh docs/status-export.json from the live state (R2360).

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

NOW = datetime.strptime("2026-11-02T03:36:10", "%Y-%m-%dT%H:%M:%S")
STAMP = "2026-11-02T03:36:10+08:00"
DUE = (NOW + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S+08:00")

DO = (
    "R2360 verification window: the debt gate named the carried battery and it "
    "ran first on the committed bc4334fa tree with zero product edits, reading "
    "RUNNER PASS 489/489 suites plus controls 7/7 in 881.8s with criteria total "
    "3910 exactly as pre-registered from R2359's shipped suite. The four "
    "follow-up sections then PASSED after the designed matrix FAIL and its "
    "regeneration, for VERDICT R2360 PASS."
)

ARTIFACT = (
    "qa/reconcile-all-R2360.log (799502B, single writer utf-8 LF through "
    "src/os/battery_stream.py) - RUNNER PASS 489/489 suites plus controls 7/7 "
    "in 881.8s with TMP RECLAIM 932/932 worlds 326.59 MiB busy=0 failed=0; "
    "docs/sandbox-suite-matrix.md regenerated to 489 suites / 3910 criteria "
    "(46795B, green=489/489) and re-read byte-identical, with the 28-byte "
    "shrink named as the evidence leg moving from the R2358-retry log to this "
    "round own battery log."
)

NEXT = (
    "R2361: the product face resuming at state/queue/tech.md:403 prefix "
    "AC-SGS1 (stamp_exempt_seed_guard_wire), whose six criteria were pinned in "
    "that row at R2346 BEFORE any code - the seed generator of "
    "state/queue/stamp_exempt.json goes through the same pinned-text guard the "
    "append and prune writers already ask."
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
        "qa/reconcile-all-R2360.log", "on",
        "R2360 verification: the battery on the committed tree reads RUNNER "
        "PASS 489/489 suites with 3910 criteria exactly as pre-registered, "
        "881.8s, and the four follow-up sections close on VERDICT PASS",
    ])
    data["results"].append([
        "R2360",
        "verification window: the carried battery ran FIRST on the committed "
        "bc4334fa tree with zero product edits (the R2168 mixed-tree rule) - "
        "RUNNER PASS 489/489 suites plus controls 7/7 in 881.8s with criteria "
        "total 3910 exactly as pre-registered from R2359 os-review-window-"
        "history-wire, TMP RECLAIM 932/932 worlds 326.59 MiB busy=0 failed=0; "
        "four follow-up sections PASS after the designed matrix FAIL and its "
        "regeneration to 46795B at 489/3910 (matrix byte-identical, "
        "fingerprint CLEAN 5 domains, profile byte-identical, census "
        "DRIFT-CLEAN) for VERDICT R2360 PASS; the 28-byte matrix shrink is "
        "named as the evidence leg moving, not a drift; the first attempt was "
        "cancelled by a filtered pipeline and wrote no evidence, rerun "
        "unfiltered; battery row closed and reconcile-battery-R2361 opened "
        "first=yes; zero product code, 0 product points",
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
    print("EXPORT R2360 self_drive=%s" % json.dumps(data["self_drive"]))
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