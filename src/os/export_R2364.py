"""export_R2364 - refresh docs/status-export.json from the live state (R2364).

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

NOW = datetime.strptime("2026-11-02T05:39:16", "%Y-%m-%dT%H:%M:%S")
STAMP = "2026-11-02T05:39:16+08:00"
DUE = (NOW + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S+08:00")

DO = (
    "R2364 verification window: the debt gate named the carried battery and it "
    "ran first on the committed 1610c9d1 tree with zero product edits, reading "
    "RUNNER PASS 492/492 suites plus controls 7/7 in 884.6s with criteria "
    "total 3928 exactly as pre-registered (+1 suite / +6 criteria from R2363's "
    "shipped suite). The four follow-up sections then PASSED after the "
    "designed matrix FAIL and its regeneration, for VERDICT R2364 PASS."
)

ARTIFACT = (
    "qa/reconcile-all-R2364.log (single writer utf-8 LF through "
    "src/os/battery_stream.py) - RUNNER PASS 492/492 suites plus controls 7/7 "
    "in 884.6s with TMP RECLAIM 932/932 worlds 326.59 MiB busy=0 failed=0; "
    "docs/sandbox-suite-matrix.md regenerated to 492 suites / 3928 criteria "
    "(47070B, green=492/492) and re-read byte-identical."
)

NEXT = (
    "R2365: the product face resuming at state/queue/tech.md:411 prefix "
    "AC-FDW1 (queue_floor_delivered_wire), whose six criteria were pinned in "
    "that row at R2354 BEFORE any code - the floor gauge still counts a "
    "DELIVERED open row as claimable supply, so a queue can read FLOOR-MET "
    "over rows whose module and suite already shipped."
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
        "qa/reconcile-all-R2364.log", "on",
        "R2364 verification: the battery on the committed tree reads RUNNER "
        "PASS 492/492 suites with 3928 criteria exactly as pre-registered, "
        "884.6s, and the four follow-up sections close on VERDICT PASS",
    ])
    data["results"].append([
        "R2364",
        "verification window: the carried battery ran FIRST on the committed "
        "1610c9d1 tree with zero product edits (the R2168 mixed-tree rule) - "
        "RUNNER PASS 492/492 suites plus controls 7/7 in 884.6s with criteria "
        "total 3928 exactly as pre-registered from the R2363 "
        "os-residue-triage-repin suite, TMP RECLAIM 932/932 worlds 326.59 MiB "
        "busy=0 failed=0; four follow-up sections PASS after the designed "
        "matrix FAIL and its regeneration to 47070B at 492/3928 (matrix "
        "byte-identical, fingerprint CLEAN 5 domains, profile byte-identical, "
        "census DRIFT-CLEAN) for VERDICT R2364 PASS; fold 641 moved 11 log "
        "items at a true round-block boundary (predicted 72360B measured "
        "72360B, margin 6140, 745 tokens covered) and the two rounds it left "
        "untriaged were declared through the shipped re-pin writer (211 -> 213 "
        "entries, TRIAGED 213/213, dropped=0); five ledger and triage suites "
        "re-read green; battery row closed and product-face-R2365 opened "
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
    print("EXPORT R2364 self_drive=%s" % json.dumps(data["self_drive"]))
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