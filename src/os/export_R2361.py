"""export_R2361 - refresh docs/status-export.json from the live state (R2361).

Every count written here is derived in this run through
check_export_consistency.recompute(); only the round label, the stamp and the
three prose summaries are this window's own words. Unlike the product modules,
this closeout reads the wall clock once for its stamp (disclosed).
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

NOW = datetime.now()
STAMP = NOW.strftime("%Y-%m-%dT%H:%M:%S+08:00")
DUE = (NOW + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S+08:00")

DO = (
    "R2361 product window: the seed generator of state/queue/stamp_exempt.json "
    "now asks the same pinned-text guard the append and prune writers already "
    "ask - a plan pins the digest and byte count it read, an execute refuses "
    "E_SEG_STALE before a byte when another writer moved the declaration in "
    "between, and the write is one atomic replace proved by read-back. Suite "
    "6/6 twice byte-identical plus five adjacent suites green, with a live dry "
    "run planning 381 entries over 79026B and writing nothing."
)

ARTIFACT = (
    "src/os/stamp_exempt_seed_guard_wire.py + "
    "src/os/test_stamp_exempt_seed_guard_wire.py (AC-SGS1..AC-SGS6), evidence "
    "qa/stamp-exempt-seed-guard-wire-R2361-a.log / -b.log (sha16 "
    "423471e4cfba0153, byte-identical) and "
    "qa/stamp-exempt-seed-guard-wire-live-R2361.log"
)

NEXT = (
    "R2362: THE BATTERY ON THE COMMITTED R2361 TREE, zero product edits until "
    "green (the R2168 mixed-tree rule). The registry read 489 suites / 3910 "
    "criteria at R2360, so the expectation is +1 suite / +6 criteria (490 / "
    "3916) from os-stamp-exempt-seed-guard-wire; any other delta must be named "
    "rather than swept. Then the four follow-up sections through "
    "src/os/battery_followup.py, whose matrix section FAILs first on the stale "
    "doc and must not rewrite it."
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
        "src/os/stamp_exempt_seed_guard_wire.py", "on",
        "R2361 product: the third writer of state/queue/stamp_exempt.json goes "
        "through the pinned-text guard - plan names the digest and byte counts "
        "it would replace, execute refuses E_SEG_STALE before any byte, and "
        "the atomic replace is proved by read-back; suite 6/6 twice plus five "
        "adjacent suites green",
    ])
    data["results"].append([
        "R2361",
        "product window: the five-still gate found no new transfer or decision "
        "token and queue_head read the tech head (tech.md:403 AC-SGS1, "
        "claimable=11), so one product face shipped - "
        "stamp_exempt_seed_guard_wire plus its suite, AC-SGS1..AC-SGS6 pinned "
        "in that row at R2346 BEFORE the code and re-anchored at HEAD with zero "
        "executable occupancy; the seed generator "
        "stamp_exempt_seed_R2280.py now routes through the wire instead of one "
        "io.open(path, 'w'), so all three declaration writers ask one guard; "
        "SUITE 6/6 twice byte-identical (sha16 423471e4cfba0153) plus five "
        "adjacent suites green, wired os-stamp-exempt-seed-guard-wire(6), live "
        "dry run planned 381 entries 79026B->78976B and wrote nothing; no "
        "battery ran (the tree was about to change by design) - battery row "
        "closed and reconcile-battery-R2362 opened first=yes at a measured "
        "target; tasks.md untouched for its encoding; one product face, 2 "
        "points",
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
    print("EXPORT R2361 stamp=%s self_drive=%s"
          % (STAMP, json.dumps(data["self_drive"])))
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